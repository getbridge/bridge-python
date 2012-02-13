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
