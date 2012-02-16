import reference

def serialize(bridge, obj):
    # obj -> function || Ref || [obj] || {str: obj} || atom
    pass

def parse_server_cmd(bridge, obj):
    chain = obj['destination']['ref']
    args = deserialize(bridge, obj['args'])
    service = reference.get_service(bridge, chain)
    return service._ref, args

def deserialize(bridge, obj):
    for container, key, ref in find_refs(obj):
        chain = ref['ref']
        try:
            service = reference.get_service(chain)
        except:
            ops = ref.get('operations', [])
            service = reference.RemoteService(bridge, ops)
            service._ref = reference.RemoteRef(bridge, chain, service)
            name = chain[reference.SERVICE]
            bridge._children[name] = service
        finally:
            container[key] = service._ref

def find_refs(obj):
    # obj -> [obj] || {str: obj} || atom
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

