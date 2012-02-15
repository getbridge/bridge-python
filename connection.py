from tornado import ioloop
from tornado.netutil import TCPServer
from tornado.escape import json_encode, json_decode, utf8

DEFAULT_EXCHANGE = 'T_DEFAULT'

class BridgeTCP(TCPServer):
    def handle_stream(self, ios, addr):

        self.bridge.log.info('Established connection with %s.' % (addr))

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
            self.loop.add_timeout(self.interval, self.reconnect)

    def send(self, msg):
        pass


