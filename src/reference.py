import types
import logging

TYPE    = 0
ROUTE   = 1
SERVICE = 2
METHOD  = 3

class Ref(object):
    def __init__(self, bridge, chain, service):
        self._bridge = bridge
        self._chain = chain
        self._service = service

    def __call__(self, *args):
        raise NotImplemented()

    def _to_dict(self):
        val = {
            'ref': self._chain,
        }
        if is_method_ref(self):
            val['operations'] = self._get_ops()
        return val

    def _get_ops(self):
        raise NotImplemented()

class LocalRef(Ref):
    def __getattr__(self, name):
        try:
            return getattr(self._service, name)
        except AttributeError:
            logging.error('Local %s does not exist.' % (name))

    def __call__(self, *args):
        if is_method_ref(self):
            method = self._chain[METHOD]
        else:
            method = 'callback'
        func = self._service[method]
        func(*args)

    def _get_ops(self):
        return [fn for fn in dir(self._service)
                    if not fn.startswith('_') and
                        type(getattr(self, fn)) == types.FunctionType]

class RemoteRef(Ref):
    def __getattr__(self, name):
        if not self._service._ops or name in self._service._ops:
            return lambda *args: self._rpc(self._chain + [name], args)
        else:
            logging.error('Remote %s does not exist.' % (name))
            return lambda *args: None

    def __call__(self, *args):
        self._rpc(self._chain, args)

    def _rpc(self, pathchain, args):
        old_chain = self._chain
        self._chain = pathchain
        self._bridge._send(args, self)
        self._chain = old_chain

    def _get_ops(self):
        return self._service._ops

class Service(object):
    def __init__(self):
        self._ref = None

    def __call__(self, *args):
        if hasattr(self, 'callback'):
            self.callback(*args)
        else:
            logging.error('Invalid method call on %s.', self._ref)

class RemoteService(Service):
    def __init__(self, ops):
        self._ops = ops

def get_service(bridge, chain):
    name = chain[SERVICE]
    return bridge._children.get(name)

def is_method_ref(ref):
    return len(ref._chain) == 4
