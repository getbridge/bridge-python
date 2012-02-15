import aux
import connection
import reference

import logging
from collections import defaultdict

class Bridge(object):
    def __init__(self, **kwargs):
        self.host = kwargs.get('host', 'localhost')
        self.port = kwargs.get('port', 8090)
        self.reconnect = kwargs.get('reconnect', True)
        self.log = logging.getLogger(__name__)
        self.log.setLevel(kwargs.get('log_level', logging.ERROR))
        self.connected = False
        self._events = defaultdict(list)
        self._children = {
            'system': _System(self)
        }
        self._connection = connection.Connection(self)

    def publish_service(self, name, service, func):
        if name in self_children:
            self.log.error('Invalid service name: "%s".', name)
        else:
            self._children[name] = service
            chain = ['named', name, name]
            ref = reference.LocalRef(self, chain, service)
            service._set_ref(ref)
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
        msg = {
            'command': 'JOINCHANNEL',
            'data': {
                'name': name,
                'handler': aux.serialize(self, handler),
                'callback': aux.serialize(self, func),
            },
        }
        self._connection.send(msg)

    def get_service(self, name, func):
        msg = {
            'command': 'GETOPS',
            'data': {
                'name': 'channel:' + name,
                'callback': aux.serialize(self, func),
            },
        }
        self._connection.send(msg)

    def get_channel(self, name, func):
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
                'callback': aux.serialize(self, _helper),
            },
        }
        self._connection.send(msg)

    def get_client_id(self):
        return self._connection.client_id

    def on(self, name, func):
        self._events[name].append(func)
        return self

    def emit(self, name, *args):
        if name in self._events:
            for func in self._events[name]:
                func(*args)
        return self

    def remove_event(self, name, func):
        if name in self._events:
            self._events[name].remove(func)
        return self

    def ready(self, func):
        if not self.connected:
            self.on('ready', func)
        else:
            func()

    def _send(self, args, destination_ref):
        msg = {
            'command': 'SEND',
            'data': {
                'args': aux.serialize(self, args),
                'destination': aux.serialize(self, destination_ref),
            },
        }
        self._connection.send(msg)

    def _on_ready(self):
        self.log.info('Handshake complete.')
        if not self.connected:
            self.connected = True
            self.emit('ready')

    def _on_message(self, obj):
        aux.deserialize(self, obj)
        destination_ref = obj.get('destination', None)
        if isinstance(destination_ref, reference.Ref):
            args = obj.get('args', [])
            destination_ref._apply_method(args)
        else:
            self.log.error('No destination in message %s.', obj)

class Service(object):
    def __init__(self, bridge):
        self.bridge = bridge

    def _get_ref(self):
        return self._ref

    def _set_ref(self, ref):
        self._ref = ref

class _System(Service):
    def __init__(self, bridge):
        super().__init__(bridge)
        chain = ['named', 'system', 'system']
        self._ref = reference.LocalRef(bridge, chain, self)

    def hook_channel_handler(self, name, handler, func=None):
        service = handler._get_service()
        self.bridge._children['channel:' + name] = service
        if func:
            chain = ['channel', name, 'channel:' + name]
            ref = reference.LocalRef(self, chain, service)
            func(ref, name)

    def getservice(self, name, func):
        if name in self.bridge._children:
            func(self.bridge._children[name])
        else:
            func(None, 'Cannot find service %s.' % (name))

    def remoteError(self, msg):
        self.bridge.log.error(msg)
        self.bridge.emit('remoteError', msg)

class _RemoteService(Service):
    def __init__(self, bridge, ops):
        super().__init__(bridge)
        self._ops = ops

