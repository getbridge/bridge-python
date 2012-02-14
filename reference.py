import copy

'''
Reference is what you actually call whenever you 'call a method' that goes over rpc. It is the proxy object.

When you implement a service, the methods are stored in a Service class. If you initialize a Reference by passing it a Service, it should inspect all of the methods in the service and pull the ones that do not have leading underscores '_<foo>' into a method dispatch dictionary. So when you do publish_service, you should make a Reference of yourself and keep it :-) -- that way you can give it to people if they ask nicely.

Service itself should not have obfuscated dispatch tables / __getattribute__ logic. Just something short and sweet developers subclass.



'''

class Reference(object):


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


