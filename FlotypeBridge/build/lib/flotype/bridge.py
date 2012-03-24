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
        # XXX: Temporary, until gateway is updated.
        self.hook_channel_handler = self.hookChannelHandler

    def hookChannelHandler(self, name, handler, func=None):
        chain = ['channel', name, 'channel:' + name]
        self._bridge._store['channel:' + name] = handler._service
        if func:
            func(handler._service, name)

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

        @param callback Called when the event loop starts. (Optional.)
        @param kwargs Specify optional config information.
            - api_key Bridge cloud api key. No default.
            - log Specifies a log level. Defaults to logging.WARNING.
            - redirector Bridge redirector. Defaults to
            http://redirector.flotype.com.
            - host Bridge host. No default. Set a value to disable redirector
            based connect.
            - port Bridge port. No default. Set a value to disable redirector
            based connect.
            - reconnect Defaults to True to enable reconnects.
        '''
        # Set configuration options.
        self._options = {}
        self._options['api_key'] = kwargs.get('api_key')
        self._options['log'] = kwargs.get('log', logging.WARNING)
        redirector = kwargs.get('redirector', 'http://redirector.flotype.com')
        self._options['redirector'] = redirector
        self._options['host'] = kwargs.get('host')
        self._options['port'] = kwargs.get('port')
        self._options['reconnect'] = kwargs.get('reconnect', True)
        self.Service = Service

        # Correct and set logging level.
        util.set_log_level(self._options)

        # Manage objects containing shared references.
        self._store = {
            'system': _System(self)
        }

        # Indicate whether the client is ready to send messages.
        self._ready = False

        # Initialize communication layer.
        self._connection = connection.Connection(self)

        # Store event handlers.
        self._events = defaultdict(list)

        if callback:
            self.on('ready', callback)

    def _execute(self, address, args):
        obj = self._store[address[2]]
        func = getattr(obj, address[3])
        util.wrapped_exec(func, 'Bridge.execute', *args)

    def _store_object(self, handler, ops):
        name = util.generate_guid()
        self._store[name] = handler
        chain = ['client', self._connection.id_promise, name]
        return reference.Reference(self, chain, ops)

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

    def add_callback(self, func, delta):
        '''Inserts a callback into the event lop, to be run
        after some time delta.

        @param func Any function of no arguments.
        @param delta A timedelta or exact datetime object.
        '''
        self._connection.loop.add_timeout(delta, func)

    def _send(self, args, destination):
        args = list(args)
        self._connection.send_command('SEND', {
            'args': args,
            'destination': destination,
        })

    def publish_service(self, name, handler, callback=None):
        '''Publish a service to Bridge.

        @param name The name of the service.
        @param service Any class with a default constructor, or any instance.
        @param callback Called (with no arguments) when the service has been
        published.
        '''
        if name == 'system':
            logging.error('Invalid service name: "%s"' % (name))
        else:
            self._store[name] = handler
            data = {'name': name}
            if callback:
                data['callback'] = callback
            self._connection.send_command('JOINWORKERPOOL', data)

    def get_service(self, name):
        '''Fetch a service from Bridge.

        @param name The service name.
        @return An opaque reference to a service.
        '''
        # Diverges from JS implementation because of catch-all getters.
        return reference.Reference(self, ['named', name, name])

    def get_channel(self, name):
        '''Fetch a channel from Bridge.

        @param name The name of the channel.
        @return An opaque reference to a channel.
        '''
        # Diverges from JS implementation because of catch-all getters.
        self._connection.send_command('GETCHANNEL', {'name': name})
        object_id = 'channel:' + name
        return reference.Reference(self, ['channel', name, object_id])

    def join_channel(self, name, handler, callback=None):
        '''Register a handler with a channel.

        @param name The name of the channel.
        @param handler An opaque reference to a channel.
        @param callback Called (with no arguments) after the handler has been
        attached to the channel.
        '''
        data = {'name': name, 'handler': handler}
        if callback:
            data['callback'] = callback
        self._connection.send_command('JOINCHANNEL', data)

    def leave_channel(self, name, handler, callback=None):
        '''Remove yourself from a channel.

        @param name The name of the channel.
        @param handler An opaque reference to a channel.
        @param callback Called (with no arguments) after the handler has been
        attached to the channel.
        '''
        data = {'name': name, 'handler': handler}
        if callback:
            data['callback'] = callback
        self._connection.send_command('LEAVECHANNEL', data)

    def ready(self, func):
        '''Entry point into the Bridge event loop.

        func is called when this node has established a connection to a Bridge
        instance. This function does not return.

        @param func Called (with no arguments) after initialization.
        '''
        if not self._ready:
            self.on('ready', func)
            self.connect()
        else:
            util.wrapped_exec(func, 'Bridge.ready')

    def connect(self):
        '''Entry point into the Bridge event loop.

        This function starts the event loop. It will eventually execute
        handlers for the 'ready' event. It does not return.
        '''
        logging.debug('Bridge.connect called.')
        self._connection.start()

    def _on_ready(self):
        logging.info('Handshake complete.')
        if not self._ready:
            self._ready = True
            self.emit('ready')
            self.remove_event('ready')
