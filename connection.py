class Connection(object):
    DEFAULT_EXCHANGE = 'T_DEFAULT'

    def __init__(self, bridge):
        self.bridge = bridge
        self.establish_connection()

    def reconnect(self):
        self.bridge.log.info('Attempting reconnect.')
        if not self.connected and self.interval < 12800:
            self.establish_connection()
            self.interval *= 2
            reactor.callLater(self.interval, self.reconnect)

    def establish_connection(self):
        self.bridge.log.info('Starting TCP connection (%s:%s).',
                             self.bridge.host, self.bridge.port)
        self.sock =

