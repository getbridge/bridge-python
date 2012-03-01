import logging
import traceback
from collections import defaultdict

import util
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
        @param api_key Bridge cloud api key. No default.
        @param redirector Bridge redirector. Defaults to http://localhost/.
        @param host Bridge host. No default. Set a value to disable redirector
        based connect.
        @param port Bridge port. No default. Set a value to disable redirector
        based connect.
        @param reconnect Defaults to True to enable reconnects.
        @param log_level Defaults to logging.ERROR.
        @var self.connected Connection state. Initially False. Set to True
        when a connection is established.
        '''
        self.api_key = kwargs.get('api_key')
        self.redirector = kwargs.get('redirector', 'http://redirector.flotype.com')
        self.host = kwargs.get('host')
        self.port = kwargs.get('port')
        self.reconnect = kwargs.get('reconnect', True)
        level = kwargs.get('log_level', logging.ERROR)
        logging.basicConfig(level=level)
        self.connected = False
        self.Service = Service

        if not self.redirector.endswith('/'):
            self.redirector += '/'

        self._events = defaultdict(list)
        sysobj = _System(self)
        chain = ['named', 'system', 'system']
        self._children = {
            'system': reference.LocalRef(chain, sysobj),
        }
        self._connection = connection.Connection(self)

    def ready(self, func):
        '''Entry point into the Bridge event loop.

        func is called when this node has established a connection to a Bridge
        instance.

        @param func Called (with no arguments) after initialization.
        '''
        if not self.connected:
            self.on('ready', func)
            self._connection.establish_connection()
        else:
            util.wrapped_exec(func)

    def publish_service(self, name, service, func=None):
        '''Publish a service to Bridge.

        @param name The name of the service.
        @param service Any class with a default constructor, or any instance. 
        @param func Called (with no arguments) when the service has been
        published.
        '''
        if name in self._children:
            logging.error('Invalid service name: "%s".' % (name))
        else:
            chain = ['named', name, name]
            self._children[name] = reference.LocalRef(chain, service)
            data = {
                'name': name,
            }
            if func:
                data['callback'] = util.serialize(self, func)
            msg = {
                'command': 'JOINWORKERPOOL',
                'data': data,
            }
            self._connection.send(msg)

    def join_channel(self, name, handler, func=None):
        '''Register a handler with a channel.

        @param name The name of the channel.
        @param handler An opaque reference to a channel.
        @param func Called (with no arguments) after the handler has been
        attached to the channel.
        '''
        data = {
            'name': name,
            'handler': util.serialize(self, handler),
        }
        if func:
            data['callback'] = util.serialize(self, func)
        msg = {
            'command': 'JOINCHANNEL',
            'data': data,
        }
        self._connection.send(msg)

    def leave_channel(self, name, handler, func=None):
        '''Remove yourself from a channel.

        @param name The name of the channel.
        @param handler An opaque reference to a channel.
        @param func Called (with no arguments) after the handler has been
        attached to the channel.
        '''
        data = {
            'name': name,
            'handler': handler._to_dict(),
        }
        if func:
            data['callback'] = util.serialize(self, func)
        msg = {
            'command': 'LEAVECHANNEL',
            'data': data,
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

    def get_channel(self, name):
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
        self._events[name].append(func)

    def emit(self, name, *args):
        '''Triggers an event.

        @param name The name of the event to trigger.
        @param args A list of arguments to the event callback.
        '''
        if name in self._events:
            for func in self._events[name]:
                util.wrapped_exec(func, 'Bridge.emit', *args)

    def clear_event(self, name):
        '''Removes the callbacks for the given event.

        @param name Name of an event.
        '''
        self._events[name] = []

    def _send(self, args, chain_dict):
        args = list(args)
        args = util.serialize(self, args)
        msg = {
            'command': 'SEND',
            'data': {
                'args': args,
                'destination': chain_dict,
            },
        }
        self._connection.send(msg)

    def _on_message(self, obj):
        try:
            ref, args = util.parse_server_cmd(self, obj)
            if callable(ref):
                util.wrapped_exec(ref, 'Bridge._on_message', *args)
        except:
            logging.error('Bad message from server in Bridge._on_message.')

class Service(object):
    '''Subclassed for type-checking purposes.'''
    pass

class _System(Service):
    def __init__(self, bridge):
        self._bridge = bridge

    def hook_channel_handler(self, name, handler, func=None):
        chain = ['channel', name, 'channel:' + name]
        ref = reference.LocalRef(chain, handler._service)
        self._bridge._children['channel:' + name] = ref
        if func:
            func(ref, name)

    def getservice(self, name, func):
        if name in self._bridge._children:
            func(self.bridge._children[name])
        else:
            func(None, 'Cannot find service %s.' % (name))

    def remoteError(self, msg):
        logging.error(msg)
        self._bridge.emit('remote_error', msg)
