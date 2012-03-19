import logging

TYPE    = 0
ROUTE   = 1
SERVICE = 2
METHOD  = 3


class Reference(object):

    def __init__(self, bridge, address, operations=[]):
        self._address = address
        self._operations = operations
        self._bridge = bridge

    def _to_dict(self, op=None):
        val = {}
        address = self._address
        if op:
            address = self._address + [op]
        val['ref'] = address
        if not is_method_address(address):
            val['operations'] = self._operations
        return val

    def __getattr__(self, op):
        func = lambda *args: self._call(op, args)
        func._reference = self
        return func

    def _call(self, op, args):
        logging.info('Calling %s.%s', self._address, op)
        self._bridge._send(args, self._to_dict(op))

def is_method_address(address):
    return len(address) == 4
