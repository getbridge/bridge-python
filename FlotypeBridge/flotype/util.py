import types
import random
import string
import logging
import traceback

from flotype import reference


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


def set_log_level(options):
    level = options.get('log', 0)
    log_level = {
        0: logging.CRITICAL,
        1: logging.ERROR,
        2: logging.WARNING,
        3: logging.INFO,
    }.get(level, logging.DEBUG)
    logging.basicConfig(level=log_level)


def is_nonprimitive(bridge, obj):
    return isinstance(obj, reference.Reference) or callable(obj) \
        or isinstance(obj, bridge.Service) or isinstance(obj, list) \
        or isinstance(obj, dict)


def serialize(bridge, obj):
    def atomic_matcher(key, val):
        return is_nonprimitive(bridge, val)
            
    if isinstance(obj, dict) or isinstance(obj, list):
        for container, key, val in deep_scan(obj, atomic_matcher):
            container[key] = serialize(bridge, val)
        return obj
    elif isinstance(obj, reference.Reference):
        return obj._to_dict()
    elif callable(obj):
        if getattr(obj, '_reference', None) is not None:
            return obj._reference._to_dict()
        else:
            handler = Callback(obj)
            return bridge._store_object(handler, find_ops(handler))._to_dict()
    elif is_nonprimitive(bridge, obj):
        return bridge._store_object(obj, find_ops(obj))._to_dict()
    else:
        logging.warn('Object not serializable')
        return obj


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
