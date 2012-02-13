import copy

class Reference(object):
    TYPE    = 0
    ROUTE   = 1
    SERVICE = 2
    METHOD  = 3

    def __init__(self, bridge, chain=None):
        if chain:
        self.bridge = bridge
            self.chain = chain
        else:
            self.chain = ['', '', '', '']

    def rpc_to_json(self, method, args):
        destination = copy.copy(self.chain)
        destination[Reference.METHOD] = method
        return {
            'command': 'SEND',
            'data': {
                'destination': destination,
                'args': args,
            }
        }


def serialize(bridge, obj):
    pass

def deserialize(bridge, obj):
    if type(obj) is dict:
        for key, val in obj:
            if type(val) is dict and 'ref' in val:
                ref = bridge.getPathObj(val['ref'])
                obj[key] = ref._setOps(val.get('operations', []))
            else:
                deserialize(bridge, obj[key])
    else:
        for elt in obj:
            deserialize(bridge, elt)


