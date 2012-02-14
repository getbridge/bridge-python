from tornado import ioloop
from tornado.netutil import TCPServer
from tornado.escape import json_encode, json_decode, utf8

DEFAULT_EXCHANGE = 'T_DEFAULT'

class BridgeTCP(TCPServer):
    def handle_stream(self, ios, addr):
        pass

class Connection(object):
    def __init__(self, bridge):
        self.bridge = bridge
        self.loop = ioloop.IOLoop.instance()
        self.server = BridgeTCP()
        self.server.listen(bridge.port, bridge.host)
        self.bridge.log.info('Started TCP connection (%s:%s).',
                             self.bridge.host, self.bridge.port)

        self.loop.add_callback(bridge.onReady)
        self.loop.start()

    def reconnect(self):
        self.bridge.log.info('Attempting reconnect.')
        if not self.connected and self.interval < 12800:
            self.establish_connection()
            self.interval *= 2
            reactor.callLater(self.interval, self.reconnect)

    def get_queue_name(self):
        return 'C_%d' % (self.client_id)

    def get_exchange_name(self):
        return 'T_%d' % (self.client_id)

    def send(self, msg):
        pass


