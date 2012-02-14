

class LocalService(Service):
    pass

class 


class Service(object):
    def __init__(self, bridge):
        self.bridge = bridge
        self.pathchain = ['', '', '', '']
        # XXX:
        # self.ref = ?

    def _get_reference(self):
        # XXX:
        # just return our reference
        pass

    def _set_reference(self, ref=None, chain=None):
        # XXX:
        # if we have ref;
        # -- replace our ref with the arg
        # -- (if this happens, this should be a new service, with
        # no methods implemented)
        # if we have chain;
        # -- update our ref's pathchain and method dispatch
        # -- (do the method dispatch bit by inspecting the methods
        # implemented in self! then tell ref about these methods)
        pass

class _System(object):
    def __init__(self, bridge):
        self.bridge = bridge

    def hook_channel_handler(self, name, handler, func=None):
        service_name = handler.pathchain.service
        service = self.bridge._children[service_name]
        self.bridge._children['channel:' + name] = service
        if func:
            func(self.bridge.getChannel(name), name)

    def get_service(self, name, func):
        if name in self.bridge._children:
            func(self.bridge._children[name])
        else:
            func(None, 'Cannot find service {0}.'.format(name))

    def remote_error(self, msg):
        self.bridge.log.warn(msg)
        self.bridge.emit('remoteError', msg)
