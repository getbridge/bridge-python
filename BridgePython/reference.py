import logging


class Reference(object):
    def __init__(self, bridge, address, operations=[]):
        self._address = address
        # Store operations supported by this reference if any
        self._operations = operations
        self._bridge = bridge

    def _to_dict(self, op=None):
        # Serialize the reference
        val = {}
        address = self._address
        # Add a method name to address if given
        if op:
            address = self._address + [op]
        val['ref'] = address
        # Append operations only if address refers to a handler
        if len(address) != 4:
            val['operations'] = self._operations
        return val

    def __getattr__(self, op):
        # Create lambda that executes RPC call with requested pathchain
        func = lambda *args: self._call(op, args)
        func._reference = self
        return func

    def _call(self, op, args):
        logging.info('Calling %s.%s', self._address, op)
        self._bridge._send(args, self._to_dict(op))
