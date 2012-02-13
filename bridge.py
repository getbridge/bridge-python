# XXX
# package twisted and simplejson

import aux
import service
import connection
import reference

import logging
from collections import defaultdict

from twisted.internet import reactor

class Bridge(object):
    def __init__(self, **kwargs):
        self.log = logging.getLogger(__name__)
        self.log.setLevel(kwargs.get('logLevel', logging.ERROR))
        self.reconnect = kwargs.get('reconnect', True)

        self._events = defaultdict(list)
        self._connected = False
        self._connection = connection.Connection(self)
        self._children = {
            'system': service._System(self)
        }

        # Client-only.
        self.url = kwargs.get('url', 'http://localhost:8080/bridge')

        # Server-only.
        self.host = kwargs.get('host', 'localhost')
        self.port = kwargs.get('port', 8090)

    def publish_service(self, name, service, func):
        if name in self_children:
            self.log.error('Invalid service name: "%s".', name)
            return

        service.set_chain(['named', name, name])
        self.connection.publish_service(name, func)
        self._children[name] = service
        return service.get_reference()

    def join_channel(self, name, handler, func):
        serialize(self, handler)

        pass

    def get_service(self, name, func):
        pass

    def get_channel(self, name):
        pass

    def get_client_id(self):
        pass

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
        pass

    def _on_ready(self):
        self.log.info('Handshake complete.')
        if not self.connected:
            self.connected = True
            self.emit('ready')

    def _on_message(self, obj):
        ref.deserialize(self, obj)
        destination = obj.get('destination', None)
        if destination and type(destination) is Ref:
            chain = destination._getChain()
            self.execute(chain, obj.get('args', []))
        else:
            self.log.warning('No destination in message %s.', obj)

    def _execute(self, chain, args):
        service = self._children[chain[ref.SERVICE]]
        func = getattr(service, chain[ref.METHOD], None)
        if func:
            func(service, *args)
        else:
            self.log.warning('Specified pathchain does not exist: %s.', chain)
