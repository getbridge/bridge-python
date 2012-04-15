import types
import random
import string
import logging
import traceback

from flotype import reference, util



class Callback(object):
    def __init__(self, func):
        # We need a wrapper object to avoid binding func as a method.
        self.wrap = (func,)
  
    def callback(self, *args):
        # Callback method so callbacks make sense to statically typed languages
        cb = self.wrap[0]
        cb(*args)

def serialize(bridge, obj):
    # Enumerate array and serialize each member
    if type(obj) == list:
        return [serialize(bridge, elt) for elt in obj]
    # Enumerate hash and serialize each member
    elif type(obj) == dict:
        return {key: serialize(bridge, val) for key, val in obj.items()}
    else:
        return serialize_atom(bridge, obj)


def serialize_atom(bridge, atom):
    # Store as callback if callable
    if callable(atom):
        return bridge._store_object(Callback(atom), ['callback'])._to_dict()
    # Call to_dict if reference
    elif isinstance(atom, reference.Reference):
        return atom._to_dict()
    # If not JSON serializeable store as service
    elif not util.is_primitive(atom):
        return bridge._store_object(atom, util.find_ops(atom))._to_dict()
    else:
        return atom

def unserialize(bridge, obj):
    # If object has ref key, convert to reference
    for container, key, ref in util.deep_scan(obj, util.ref_matcher):
        address = ref['ref']
        ops = ref.get('operations', [])
        if address[1] == bridge._connection.client_id and address[0] == 'client':
            container[key] = bridge._store[address[2]]
        else:           
            # Create reference
            ref = reference.Reference(bridge, address, ops)
            if ref._operations == ['callback']:
                obj = ref.callback
                obj.callback = ref.callback
                container[key] = obj
            else:
                container[key] = ref
    return obj


