import types

TYPE    = 0
ROUTE   = 1
SERVICE = 2
METHOD  = 3

class Ref(object):
    def __init__(self, bridge, chain, service):
        self._bridge = bridge
        self._chain = chain
        self._service = service

    def __call__(self, args):
        raise NotImplemented()

    def _to_dict(self):
        val = {
            'ref': self._chain,
        }
        if len(self._chain) < 4:
            val['operations'] = self._get_ops()
        return val

    def _get_ops(self):
        raise NotImplemented()

class LocalRef(Ref):
    def __getattr__(self, name):
        try:
            return getattr(self._service, name)
        except AttributeError:
            self._bridge.log.error('Local %s does not exist.' % (name))

    def __call__(self, args):
        func = self._service[self._chain[METHOD]]
        func(*args)

    def _get_ops(self):
        if hasattr(self, '_ops'):
            return self._ops

        self._ops = [fn for fn in dir(self)
                        if not fn.startswith('_') and
                            type(getattr(self, fn)) == types.FunctionType]
        return self._ops

class RemoteRef(Ref):
    def __getattr__(self, name):
        if name in self._service._ops:
            return lambda args: self._rpc(self._chain + [name], args)
        else:
            self._bridge.log.error('Remote %s does not exist.' % (name))
            return lambda args: None

    def __call__(self, args):
        self._rpc(self._chain, args)

    def _rpc(self, pathchain, args):
        self._bridge._send(args, pathchain)

    def _get_ops(self):
        return self._service._ops

class Service(object):
    def __init__(self, bridge):
        self.bridge = bridge
        self._ref = None

class RemoteService(Service):
    def __init__(self, bridge, ops):
        super().__init__(bridge)
        self._ops = ops

def get_service(bridge, chain):
    name = chain[SERVICE]
    return bridge._children[name]
