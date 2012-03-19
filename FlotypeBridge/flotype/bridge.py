import logging
import traceback
from collections import defaultdict

from flotype import util, connection, reference

'''
@package bridge
A Python API for bridge clients.
'''


class Service(object):
    '''Subclassed for type-checking purposes.'''
    pass


class _System(Service):
    def __init__(self, bridge):
        self._bridge = bridge

    def hookChannelHandler(self, name, handler, func=None):
        chain = ['channel', name, 'channel:' + name]
        ref = reference.LocalRef(chain, handler._service)
        self._bridge._store['channel:' + name] = ref
        if func:
            func(ref, name)

    def getService(self, name, func):
        if name in self._bridge._store:
            func(self._bridge._store[name], name)
        else:
            func(None, name)

    def remoteError(self, msg):
        logging.warning(msg)
        self._bridge.emit('remote_error', msg)


class Bridge(object):
    '''Interface to the Bridge server.'''

    def __init__(self, callback=None, **kwargs):
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
        self.Service = Service

        # Set configuration options
        self._options = {}
        self._options.api_key = kwargs.get('api_key')
        self._options.redirector = kwargs.get('redirector', 'http://redirector.flotype.com')
        self._options.host = kwargs.get('host')
        self._options.port = kwargs.get('port')
        self._options.reconnect = kwargs.get('reconnect', True)
        level = kwargs.get('log_level', logging.WARNING)

        # Set logging level
        logging.basicConfig(level=level)

        # Contains references to shared references
        sysobj = _System(self)
        self._store = {
            'system': reference.LocalRef(['named', 'system', 'system'], sysobj),
        }

        # Indicate whether ready
        self._ready = False

        # Communication layer
        self._connection = connection.Connection(self)

        # Store event handlers
        self._events = defaultdict(list)

        if callback is not None:
            self.ready(callback)



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

    def remove_event(self, name):
        '''Removes the callbacks for the given event.

        @param name Name of an event.
        '''
        self._events[name] = []

    def _on_ready():
        logging.info('Handshake complete')
        if not self._ready:
            self._ready = True
            self.emit('ready')

    def publish_service(self, name, service, callback=None):
        '''Publish a service to Bridge.

        @param name The name of the service.
        @param service Any class with a default constructor, or any instance. 
        @param callback Called (with no arguments) when the service has been
        published.
        '''
        if name == 'system':
            logging.error('Invalid service name: "%s"' % (name))
        else:
            self._store[name] = reference.LocalRef(['named', name, name], service)
            self.connection.send_command('JOINWORKERPOOL', {'name': name,
                'callback': callback})

    def get_service(self, name):
        '''Fetch a service from Bridge.

        @param name The service name.
        @return An opaque reference to a service.
        '''
        # Diverges from JS implementation because of catch-all getters
        return reference.RemoteRef(['named', name, name], self)

    def get_channel(self, name):
        '''Fetch a channel from Bridge.

        @param name The name of the channel.
        @return An opaque reference to a channel.
        '''
        self._connection.send_command('GETCHANNEL', {'name': name})
        service = 'channel:' + name
        # Diverges from JS implementation because of catch-all getters
        return reference.RemoteRef(['channel', name, service], self)

    def join_channel(self, name, handler, callback=None):
        '''Register a handler with a channel.

        @param name The name of the channel.
        @param handler An opaque reference to a channel.
        @param callback Called (with no arguments) after the handler has been
        attached to the channel.
        '''
        self._connection.send_command('JOINCHANNEL', {'name': name,
            'handler': handler, 'callback': callback})

    def leave_channel(self, name, handler, callback=None):
        '''Remove yourself from a channel.

        @param name The name of the channel.
        @param handler An opaque reference to a channel.
        @param callback Called (with no arguments) after the handler has been
        attached to the channel.
        '''
        self._connection.send_command('LEAVECHANNEL', {'name': name,
        'callback': callback})

    def ready(self, func):
        '''Entry point into the Bridge event loop.

        func is called when this node has established a connection to a Bridge
        instance.

        @param func Called (with no arguments) after initialization.
        '''
        if not self._ready:
            self.on('ready', func)
        else:
            util.wrapped_exec(func)
