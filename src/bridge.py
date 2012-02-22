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
    '''Interface to the Bridge server.'''

    def __init__(self, **kwargs):
        '''Initialize Bridge.

        @param kwargs Specify optional config information.
        @param host Bridge host. Defaults to 'localhost'.
        @param port Bridge port. Defaults to 8090.
        @param reconnect Defaults to True to enable reconnects.
        @param log_level Defaults to logging.ERROR.
        @var self.connected Connection state, initially False.
        '''
        self.host = kwargs.get('host', 'localhost')
        self.port = kwargs.get('port', 8090)
        self.reconnect = kwargs.get('reconnect', True)
        logging.basicConfig(level=kwargs.get('log_level', logging.ERROR))
        self.connected = False
        self._events = defaultdict(list)
        sysobj = _System(self)
        chain = ['named', 'system', 'system']
        self._children = {
            'system': reference.LocalRef(chain, sysobj),
        }
        self._connection = connection.Connection(self)

    def ready(self, func):
        '''Entry point into the Bridge event loop.

        func is called when this node has established a connection to
        a Bridge instance.

        @param func Called (with no arguments) after initialization.
        '''
        if not self.connected:
            self.on('ready', func)
            self._connection.establish_connection()
        else:
            func()

    def publish_service(self, name, service, func):
        '''Publish a service to Bridge.

        @param name The name of the service.
        @param service Any class with a default constructor, or any
        instance object. 
        @param func Called (with no arguments) when the service has
        been published.
        '''
        if name in self._children:
            logging.error('Invalid service name: "%s".' % (name))
        else:
            chain = ['named', name, name]
            self._children[name] = reference.LocalRef(chain, service)
            msg = {
                'command': 'JOINWORKERPOOL',
                'data': {
                    'name': name,
                    'callback': aux.serialize(self, func),
                },
            }
            self._connection.send(msg)

    def join_channel(self, name, handler, func):
        '''Register a handler with a channel.

        @param name The name of the channel.
        @param handler An opaque reference to a channel.
        @param func Called (with no arguments) after the handler has
        been attached to the channel.
        '''
        msg = {
            'command': 'JOINCHANNEL',
            'data': {
                'name': name,
                'handler': handler._to_dict(),
                'callback': aux.serialize(self, func),
            },
        }
        self._connection.send(msg)

    def leave_channel(self, name, handler, func):
        '''Remove yourself from a channel.

        @param name The name of the channel.
        @param handler An opaque reference to a channel.
        @param func Called (with no arguments) after the handler has
        been attached to the channel.
        '''
        msg = {
            'command': 'LEAVECHANNEL',
            'data': {
                'name': name,
                'handler': handler._to_dict(),
                'callback': aux.serialize(self, func),
            },
        }
        self._connection.send(msg)

    def get_service(self, name):
        '''Fetch a service from Bridge.

        @param name The service name.
        @return An opaque reference to a service.
        '''
        ref = reference.RemoteRef(['named', name, name], self)
        self._children[name] = ref
        return ref

    def get_channel(self, name, func):
        '''Fetch a channel from Bridge.

        @param name The name of the channel.
        @return An opaque reference to a channel.
        '''
        msg = {        
            'command': 'GETCHANNEL',
            'data': {
                'name': name,
            },
        }
        self._connection.send(msg)
        service = 'channel:' + name
        chain = ['channel', name, service]
        ref = reference.RemoteRef(chain, self)
        self._children[service] = ref
        return ref

    def get_client_id(self):
        '''Returns the client ID of this node.

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

        @param name The name of the event.
        @param func Called when this event is emitted.
        '''
        logging.debug('Registering handler for event %s.' % (name))
        self._events[name].append(func)

    def emit(self, name, *args):
        '''Triggers an event.

        @param name The name of the event to trigger.
        @param args A list of arguments to the event callback.
        '''
        logging.debug('Emitting event %s(%s).' % (name, args))
        if name in self._events:
            for func in self._events[name]:
                func(*args)

    def clear_event(self, name):
        '''Removes the callbacks for the given event.

        @param name Name of an event.
        '''
        self._events[name] = []

    def _send(self, args, chain_dict):
        print('Bridge._send: ', args)
        msg = {
            'command': 'SEND',
            'data': {
                'args': aux.serialize(self, list(args)),
                'destination': chain_dict,
            },
        }
        self._connection.send(msg)

    def _on_message(self, obj):
        try:
            destination_ref, args = aux.parse_server_cmd(self, obj)
            print('Bridge._on_message:', (destination_ref._chain, args))
            print('CURRENT CHILDREN STATE =', self._children)
            print('OK, STILL IN BRIDGE._ON_MESSAGE, ABOUT TO CALL;', destination_ref)
            destination_ref(*args)
        except aux.AuxError as err:
            print(err)
            logging.error('Received bad message from server.')
        except Exception as err:
            import traceback
            traceback.print_exc()
            print('', '*' * 40, '\n', err, '\n', '*' * 40)
            print("Unknown exception in Bridge._on_message.")

class _System(object):
    def __init__(self, bridge):
        self._bridge = bridge

    def hook_channel_handler(self, name, handler, func=None):
        print('_System.hook_channel_handler: ' + name)
        chain = ['channel', name, 'channel:' + name]
        ref = reference.LocalRef(chain, handler._service)
        self._bridge._children['channel:' + name] = ref
        if func:
            print('hook_channel_handler, func provided!')
            func(ref, name)

    def getservice(self, name, func):
        print('_System.getservice called!', name)
        if name in self.bridge._children:
            print('Service found.')
            func(self.bridge._children[name])
        else:
            print('Service not found.')
            func(None, 'Cannot find service %s.' % (name))

    def remoteError(self, msg):
        logging.error(msg)
        self.bridge.emit('remote_error', msg)
