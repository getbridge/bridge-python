import logging

TYPE    = 0
ROUTE   = 1
SERVICE = 2
METHOD  = 3

def ref_to_dict(chain, ops):
    val = {
        'ref': chain,
    }
    if not is_method_chain(chain):
        val['operations'] = ops
    return val

class Ref(object):
    def _to_dict(self):
        return ref_to_dict(self._chain, self._get_ops())

class LocalRef(Ref):
    def __init__(self, chain, service):
        self._chain = chain
        if type(service) == type:
            service = service()
        self._service = service

    def __getattr__(self, name):
        try:
            return getattr(self._service, name)
        except AttributeError:
            logging.error('Invalid call to local::%s.' % (name))

    def __call__(self, *args):
        if is_method_chain(self._chain):
            method = self._chain[METHOD]
        elif hasattr(self._service, 'callback'):
            method = 'callback'
        elif hasattr(self._service, '__call__'):
            method = '__call__'
        else:
            name = self._chain[METHOD]
            logging.error('Call to local::%s impossible.' % (name))
            return
            
        func = getattr(self._service, method)
        func(*args)
 
    def _get_ops(self):
        return [fn for fn in dir(self._service)
                    if not fn.startswith('_') and
                        callable(getattr(self, fn))]

class RemoteRef(Ref):
    def __init__(self, chain, bridge):
        self._chain = chain
        self._bridge = bridge

    def __getattr__(self, name):
        return lambda *args: self._rpc(self._chain + [name], args)

    def __call__(self, *args):
        self._rpc(self._chain, args)

    def _rpc(self, chain, args):
        if not is_method_chain(chain):
            callchain = chain + ['callback']
        else:
            callchain = chain
        self._bridge._send(args, ref_to_dict(callchain, self._get_ops()))

    def _get_ops(self):
        return []

def get_ref(bridge, chain):
    name = chain[SERVICE]
    return bridge._children.get(name, False)

def is_method_chain(chain):
    return len(chain) == 4
