import sys
import struct
import socket

from tornado import ioloop, iostream
from tornado.escape import json_encode, json_decode, utf8, to_unicode

class Connection(object):
    def __init__(self, bridge, interval=400):
        self.bridge = bridge
        self.interval = interval
        self.loop = ioloop.IOLoop.instance()
        self.establish_connection()

    def establish_connection(self):
        self.sock = socket.socket(AF_UNSPEC, socket.SOCK_STREAM, 0)
        self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.stream = iostream.IOStream(self.sock)
        self.bridge.log.info('Connecting to (%s:%s).',
                             self.bridge.host, self.bridge.port)
        self.stream.connect((bridge.host, bridge.port), self.on_connect)
        if not self.loop.running():
            self.loop.start()

    def on_connect(self):
        msg_id = getattr(self, 'client_id', 0)
        msg_secret = getattr(self, 'secret', 0)
        msg = {
            'command': 'CONNECT',
            'data': {
                'session': msg_id,
                'secret': msg_secret,
            },
        }
        self.send(msg)
        self.stream.set_close_callback(self.close_handler)
        self.wait()

    def wait(self, func):
        self.stream.read_bytes(4, self.msg_handler)

    def msg_handler(self, data):
        size = socket.ntohl(struct.unpack('>I', data)[0])
        self.stream.read_bytes(size, self.body_handler)

    def body_handler(self, data):
        self.on_message(to_unicode(data))
        self.wait()

    def on_message(self, msg):
        self.client_id, self.secret = msg.split('|')
        self.on_message = self._replacement_on_message
        self.bridge._on_ready()

    def _replacement_on_message(self, msg):
        try:
            obj = json_decode(msg)
            self.bridge._on_message(obj)
        except:
            self.bridge.log.info('Dropping corrupted message.')

    def close_handler(self):
        self.bridge.error('Connection shutdown.')
        self.bridge.connected = False
        self.loop.stop()
        if self.bridge.reconnect:
            self.reconnect()

    def reconnect(self):
        self.bridge.log.info('Attempting reconnect.')
        if not self.bridge.connected and self.interval < 12800:
            self.establish_connection()
            self.interval *= 2
            self.loop.add_timeout(self.interval, self.reconnect)

    def send(self, msg):
        data = utf8(json_encode(msg))
        size = struct.pack('>I', len(data))
        self.stream.write(size + data)
