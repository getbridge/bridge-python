TYPE    = 0
ROUTE   = 1
SERVICE = 2
METHOD  = 3

class Ref(object):
    def __init__(self, bridge, chain, service=None):
        self._bridge = bridge
        self._chain = chain
        self._service = service

    def _get_service(self):
        if self._service:
            return self._service
        else:
            name = self._chain[SERVICE]
            self._service = self._bridge._children[name]
            return self._service

    def _apply_method(self, args):
        pass

class LocalRef(Reference):
    def __getattr__(self, name):




