import reference

# obj -> function || Ref || [obj || JSON-type]

def serialize(bridge, obj):
    pass

def parse_server_cmd(bridge, obj):
    chain = obj['destination']['ref']
    args = deserialize(bridge, obj['args'])
    service = reference.get_service(bridge, chain)
    return service._ref, args

def deserialize(bridge, obj):
    for container, key, chain in find_refs(obj):
        try:
            service = reference.get_service(chain)
            container[key] = service._ref
        except:
            # Create and store a remote service with a RemoteRef.
            raise NotImplemented()

def find_refs(obj):
    # obj -> [obj], {str: obj}, atom
    iterator = []
    if type(obj) is list:
        iterator = enumerate(obj)
    elif type(obj) is dict:
        iterator = obj
    for key, val in iterator:
        if type(val) is dict and 'ref' in val:
            yield obj, key, val
        else:
            for result in find_refs(val):
                yield result

