import types
import random
import string
import logging
import traceback
import json

from tornado.escape import utf8, native_str

from BridgePython import reference

primitives = set((int, str, bool, float, tuple, list, dict, type(None)))
try:
    primitives.update((long, types.UnicodeType))
except NameError:
    pass


def is_primitive(obj):
    return type(obj) in primitives


def set_log_level(level):
    if level == 3:
        level = logging.INFO
    elif level == 2:
        level = logging.WARNING
    elif level == 1:
        level = logging.ERROR
    elif level == 0:
        level = logging.CRITICAL
    logging.basicConfig(level=level)


def generate_guid():
    return ''.join([
        random.choice(string.ascii_letters) for k in range(32)
    ])
    

def stringify(val):
    return utf8(json.dumps(val, default=str))


def parse(val):
    return json.loads(native_str(val))


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
