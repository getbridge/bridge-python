import types
import random
import string
import logging
import traceback

from flotype import reference

class UtilError(Exception):
    pass

class Callback(object):
    def __init__(self, func):
        # Cannot store it directly in self (will bind method)
        self._cbDict = {'callback': func}

    def callback(self, *args):
        cb = self._cbDict.get('callback')
        cb(*args)

def wrapped_exec(func, loc, *args):
    try:
        func(*args)
    except:
        traceback.print_exc()
        logging.error('At %s.' % (loc))

def is_function(obj):
    return type(obj) in (
        types.FunctionType, types.BuiltinFunctionType, types.BuiltinMethodType
    )

def serialize(bridge, obj):
    def atomic_matcher(key, val):
        return isinstance(val, reference.Ref) or \
            callable(val) or isinstance(val, bridge.Service)

    if type(obj) in (list, dict):
        for container, key, val in deep_scan(obj, atomic_matcher):
            container[key] = serialize(bridge, val)
        return obj
    elif isinstance(obj, reference.Ref):
        return obj._to_dict()
    elif is_function(obj):
        return serialize_callable(bridge, Callback(obj))
    elif callable(obj) or isinstance(obj, bridge.Service):
        return serialize_callable(bridge, obj)
    else:
        print(obj)
        raise UtilError('object not serializable.')

def serialize_callable(bridge, func):
    name = gen_guid()
    chain = ['client', bridge.get_client_id(), name]
    ref = reference.LocalRef(chain, func)
    bridge._children[name] = ref
    return ref._to_dict()

def generate_guid():
    return ''.join([
        random.choice(string.ascii_letters) for k in range(32)
    ])

def deserialize(bridge, obj):
    for container, key, ref in deep_scan(obj, ref_matcher):
        chain = ref['ref']
        service_ref = reference.get_ref(bridge, chain)
        if not service_ref:
            ops = ref.get('operations', [])
            name = chain[reference.SERVICE]
            service_ref = reference.RemoteRef(chain, bridge)
        container[key] = service_ref
    return obj

def ref_matcher(key, val):
    return type(val) == dict and 'ref' in val

def deep_scan(obj, matcher):
    iterator = []
    if type(obj) is dict:
        iterator = obj.items()
    elif type(obj) is list:
        iterator = enumerate(obj)
    for key, val in iterator:
        if matcher(key, val):
            yield obj, key, val
        else:
            for result in deep_scan(val, matcher):
                yield result
