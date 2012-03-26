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
        cb = self.wrap[0]
        cb(*args)

def serialize(bridge, obj):
    if type(obj) == list:
        return [serialize(bridge, elt) for elt in obj]
    elif type(obj) == dict:
        return {key: serialize(bridge, val) for key, val in obj.items()}
    else:
        return serialize_atom(bridge, obj)


def serialize_atom(bridge, atom):
    if callable(atom):
        if getattr(atom, '_reference', None) is not None:
            return atom._reference._to_dict()
        else:
            handler = Callback(atom)
            return bridge._store_object(handler, util.find_ops(handler))._to_dict()
    elif isinstance(atom, reference.Reference):
        return atom._to_dict()
    elif not util.is_primitive(atom):
        return bridge._store_object(atom, util.find_ops(atom))._to_dict()
    else:
        return atom

def unserialize(bridge, obj):
    for container, key, ref in util.deep_scan(obj, util.ref_matcher):
        address = ref['ref']
        ops = ref.get('operations', [])
        ref = reference.Reference(bridge, address, ops)
        if ref._operations == ['callback']:
            container[key] = ref.callback
        else:
            container[key] = ref
    return obj


