import sys
import struct
import socket
from collections import deque

from tornado import ioloop, iostream
from tornado.escape import json_encode, json_decode, utf8, to_unicode

class Connection(object):
    def __init__(self, bridge, interval=400):
        self.bridge = bridge
        self.interval = interval
        self.loop = ioloop.IOLoop.instance()
        self.msg_queue = deque()
        self.client_id = 0
        self.secret = 0
        self.establish_connection()

    def establish_connection(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.stream = iostream.IOStream(self.sock)
        self.bridge.log.info('Connecting to (%s:%s).',
                             self.bridge.host, self.bridge.port)
        server = (self.bridge.host, self.bridge.port)
        self.stream.connect(server, self.on_connect)
        if not self.loop.running():
            self.loop.start()

    def on_connect(self):
        msg = {
            'command': 'CONNECT',
            'data': {
                'session': [self.client_id, self.secret],
            },
        }
        self.send(msg)
        self.stream.set_close_callback(self.close_handler)
        if len(self.msg_queue):
            self.bridge.emit('reconnect')
            self.loop.add_callback(self.process_queue)
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
        self.client_id, self.secret = map(int, msg.split('|'))
        self.on_message = self._replacement_on_message
        self.bridge._on_ready()

    def _replacement_on_message(self, msg):
        try:
            obj = json_decode(msg)
            self.bridge._on_message(obj)
        except:
            self.bridge.log.info('Dropping corrupted message.')

    def close_handler(self):
        self.bridge.connected = False
        self.loop.stop()
        self.bridge.error('Connection shutdown.')
        self.bridge.emit('disconnect')
        if self.bridge.reconnect:
            self.reconnect()

    def reconnect(self):
        self.bridge.log.info('Attempting reconnect.')
        if not self.bridge.connected and self.interval < 12800:
            self.establish_connection()
            self.interval *= 2
            self.loop.add_timeout(self.interval, self.reconnect)

    def process_queue(self):
        while self.bridge.connected and len(self.msg_queue):
            buf = self.msg_queue.popleft()
            self.stream.write(buf)

    def send(self, msg):
        data = utf8(json_encode(msg))
        size = struct.pack('>I', len(data))
        buf = size + data
        if self.bridge.connected:
            self.stream.write(buf)
        else:
            self.msg_queue.append(buf)
