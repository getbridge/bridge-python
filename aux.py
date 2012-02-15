import reference

# obj -> function || Ref || [obj || JSON-type]

def serialize(bridge, obj):
    pass

def parse_server_cmd(bridge, obj):
    chain = obj['destination']['ref']
    args = deserialize(bridge, obj['args'])
    # XXX: Are we absolutely guaranteed this node has a record of
    # the specified service? If not, wrap the following line in a try
    # block, and create the (clearly remote) service (without ops?).
    service = reference.get_service(bridge, chain)
    return service._ref, args

def deserialize(bridge, obj):
    if type(obj) is dict:
        for key, val in obj:
            if type(val) is list and 'ref' in val:
                chain = val['ref']
                if len(chain) == 3:
                    name = chain[reference.SERVICE]
                    if name in bridge._children:
                        # XXX: Is it ever possible to already know
                        # an incoming remote service reference?
                        obj[key] = bridge._children[name]._ref
                    else:

                if bridge.
                ref = reference.RemoteRef(bridge, chain, None)
                try:
                    ref._service
                except:
                    # XXX: Handle missing services.
                    raise NotImplemented()

                obj[key] = ref._setOps(val.get('operations', []))
            else:
                deserialize(bridge, obj[key])
    else:
        for elt in obj:
            deserialize(bridge, elt)

