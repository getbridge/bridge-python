import copy
import logging
from collections import defaultdict

import aux
import connection
import reference

'''
@package bridge
A Python API for bridge clients.
'''

class Bridge(object):
    '''Encapsulates all interactions with the Bridge server.'''

    def __init__(self, **kwargs):
        '''Initialize Bridge.

        @param kwargs Specify optional config information.
        @param host Bridge host. Defaults to 'localhost'.
        @param port Bridge port. Defaults to 8090.
        @param reconnect Defaults to True to enable reconnects.
        @var self.connected Connection state, initially False.
        '''
        self.host = kwargs.get('host', 'localhost')
        self.port = kwargs.get('port', 8090)
        self.reconnect = kwargs.get('reconnect', True)
        self.connected = False
        self._events = defaultdict(list)
        self._children = {
            'system': _System(self)
        }
        self._connection = connection.Connection(self)

    def ready(self, func):
        '''Entry point into the Bridge event loop.

        func is called when this node has established a connection to a
        Bridge instance.

        @param func A function of no arguments, called upon initialization.
        '''
        print('Bridge.ready called.')
        if not self.connected:
            self.on('ready', func)
            self._connection.establish_connection()
        else:
            func()

    def publish_service(self, name, service, func):
        '''Publish a service to Bridge.

        @param name The name of the service.
        @param service Some instance of Service.
        @param func A callback triggered when the service has been published.
        @param func No arguments are passed to func.
        '''
        print('Bridge.publish_service called.')
        if name in self._children:
            logging.error('Invalid service name: "%s".', name)
        else:
            self._children[name] = service
            chain = ['named', name, name]
            ref = reference.LocalRef(self, chain, service)
            service._ref = ref
            msg = {
                'command': 'JOINWORKERPOOL',
                'data': {
                    'name': name,
                    'callback': aux.serialize(self, func),
                },
            }
            self._connection.send(msg)
            return ref

    def join_channel(self, name, handler, func):
        '''Register a handler with a channel.

        @param name The name of the channel.
        @param handler An opaque reference to a Service.
        @param func A callback triggered after the handler is attached.
        @param func No arguments are passed to func.
        '''
        print('Bridge.join_channel called.')
        msg = {
            'command': 'JOINCHANNEL',
            'data': {
                'name': name,
                'handler': handler._to_dict(),
                'callback': aux.serialize(self, func),
            },
        }
        self._connection.send(msg)

    def get_service(self, name, func):
        '''Fetch a service from Bridge.

        @param name The name of the requested service.
        @param func A callback triggered once the service has been received.
        @param func func is given an opaque reference to a Service.
        '''
        print('Bridge.get_service called.')
        msg = {
            'command': 'GETOPS',
            'data': {
                'name': 'channel:' + name,
                'callback': aux.serialize(self, func),
            },
        }
        self._connection.send(msg)

    def get_channel(self, name, func):
        '''Fetch a channel from Bridge.

        @param name The name of the requested channel.
        @param func A callback triggered once the channel has been received.
        @param func func is given an opaque reference and an error message.
        '''
        print('Bridge.get_channel called.')
        def _helper(service, error):
            if error:
                func(None, error)
            else:
                chain = ['channel', name, 'channel:' + name]
                func(reference.RemoteRef(self, chain, service), None)

        msg = {
            'command': 'GETOPS',
            'data': {
                'name': 'channel:' + name,
                'callback': aux.serialize_func(self, _helper),
            },
        }
        self._connection.send(msg)

    def get_client_id(self):
        '''Finds the client ID of this node.

        @return None || str
        '''
        return self._connection.client_id

    def on(self, name, func):
        '''Registers a callback for the specified event.

        Event names and arity;
        ready/0
        disconnect/0
        reconnect/0
        remote_error/1 (msg)

        @param name The name of the event to listen for.
        @param func A callback triggered when this event is emitted.
        '''
        logging.debug('Registering event %s.' % (name))
        self._events[name].append(func)
        return self

    def emit(self, name, *args):
        '''Triggers an event.

        @param name An arbitrary name of the event to be triggered.
        @param args A list of arguments to the event callback.
        '''
        logging.debug('Emitting event %s(%s).' % (name, args))
        if name in self._events:
            for func in self._events[name]:
                func(*args)
        return self

    def remove_event(self, name, func):
        '''Removes a callback for the given event name.

        @param name Name of an event.
        @param func The function object to be removed as an event handler.
        '''
        if name in self._events:
            self._events[name].remove(func)
        return self

    def _send(self, args, destination_ref):
        print('Bridge._send: ' + (args))
        msg = {
            'command': 'SEND',
            'data': {
                'args': aux.serialize(self, args),
                'destination': destination_ref._to_dict(),
            },
        }
        self._connection.send(msg)

    def _on_message(self, obj):
        try:
            destination_ref, args = aux.parse_server_cmd(self, obj)
            print('Bridge._on_message:', (destination_ref._chain, args))
            destination_ref(args)
        except aux.AuxError as err:
            print(err)
            logging.error('Received bad message from server.')
        except Exception as err:
            raise Exception
            raise Exception
            print(err)
            print("Unknown exception in Bridge._on_message.")


Service = reference.Service

class _System(Service):
    def __init__(self, bridge):
        super().__init__(bridge)
        chain = ['named', 'system', 'system']
        self._ref = reference.LocalRef(bridge, chain, self)

    def hook_channel_handler(self, name, handler, func=None):
        logging.debug('_System.hook_channel_handler: ' + name)
        service = copy.copy(handler._service)
        chain = ['channel', name, 'channel:' + name]
        ref = reference.LocalRef(self, chain, service)
        service._ref = ref
        self.bridge._children['channel:' + name] = service
        if func:
            func(ref, name)

    def getservice(self, name, func):
        if name in self.bridge._children:
            logging.debug('_System.getservice: ' + name)
            func(self.bridge._children[name])
        else:
            func(None, 'Cannot find service %s.' % (name))

    def remoteError(self, msg):
        logging.error(msg)
        self.bridge.emit('remote_error', msg)
