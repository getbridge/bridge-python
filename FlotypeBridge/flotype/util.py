import types
import random
import string
import logging
import traceback

from flotype import reference

primitives = set((int, str, bool, float, tuple, list, dict, type(None)))
try:
    primitives.update((long, types.UnicodeType))
except NameError:
    pass


class Promise(object):
    def __init__(self, root, attr):
        self.root = root
        self.attr = attr

    def __str__(self):
        return getattr(self.root, self.attr, '<EmptyPromise>')


class Callback(object):
    def __init__(self, func):
        # We need a wrapper object to avoid binding func as a method.
        self.wrap = (func,)

    def callback(self, *args):
        cb = self.wrap[0]
        cb(*args)


def wrapped_exec(func, loc, *args):
    try:
        func(*args)
    except:
        traceback.print_exc()
        logging.error('At %s.' % (loc))


def is_primitive(obj):
    return type(obj) in primitives


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
            return bridge._store_object(handler, find_ops(handler))._to_dict()
    elif isinstance(atom, reference.Reference):
        return atom._to_dict()
    elif not is_primitive(atom):
        return bridge._store_object(atom, find_ops(atom))._to_dict()
    else:
        return atom


def generate_guid():
    return ''.join([
        random.choice(string.ascii_letters) for k in range(32)
    ])


def deserialize(bridge, obj):
    for container, key, ref in deep_scan(obj, ref_matcher):
        address = ref['ref']
        ops = ref.get('operations', [])
        ref = reference.Reference(bridge, address, ops)
        if ref._operations == ['callback']:
            container[key] = ref.callback
        else:
            container[key] = ref
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


def find_ops(obj):
    return [fn for fn in dir(obj)
                if not fn.startswith('_') and
                    callable(getattr(obj, fn))]
