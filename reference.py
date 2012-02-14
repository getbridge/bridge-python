class Reference(object):
    def __init__(self, bridge, chain, service=None):
        self._bridge = bridge
        self._chain = chain
        self._service = service

    def _get_service(self):
        if self._service:
            return self._service
        else:
            self._service = self._bridge._children[self._chain[SERVICE]]

class LocalRef(Reference):
    def __getattr__(self, name):



TYPE    = 0
ROUTE   = 1
SERVICE = 2
METHOD  = 3

