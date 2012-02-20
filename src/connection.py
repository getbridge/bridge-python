import sys
import struct
import socket
import logging
from collections import deque

from tornado import ioloop, iostream
from tornado.escape import json_encode, json_decode, utf8, to_unicode

class Connection(object):
    def __init__(self, bridge, interval=400):
        self.bridge = bridge
        self.interval = interval
        self.loop = ioloop.IOLoop.instance()
        self.msg_queue = deque()
        self.client_id = None
        self.secret = None
        self.establish_connection()

    def establish_connection(self):
        print('Connection.establish_connection called.')
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.stream = iostream.IOStream(self.sock)
        logging.info('Connecting to %s:%s.' %
                     (self.bridge.host, self.bridge.port))
        server = (self.bridge.host, self.bridge.port)
        self.stream.connect(server, self.on_connect)
        if not self.loop.running():
            self.loop.start()

    def on_connect(self):
        print('Connecting.on_connect called.')
        self.bridge.connected = True
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

    def wait(self):
        print('Connecting.wait called: waiting...')
        self.stream.read_bytes(4, self.msg_handler)

    def msg_handler(self, data):
        print(b'Connecting.msg_handler called: ' + data)
        size = struct.unpack('>I', data)[0]
        print('size = %s' % (size))
        self.stream.read_bytes(size, self.body_handler)

    def body_handler(self, data):
        print(b'Connecting.body_handler called: ' + data)
        self.on_message(to_unicode(data))
        self.wait()

    def on_message(self, msg):
        try:
            self.client_id, self.secret = msg.split('|')
            print((self.client_id, self.secret))
        except:
            self.bridge.emit('remote_error', 'Bad CONNECT.')
            logging.error('Connecting.on_message: remote error!')
            self.close_handler()
            return

        self.on_message = self._replacement_on_message
        logging.info('Handshake complete.')
        self.bridge.emit('ready')

    def _replacement_on_message(self, msg):
        try:
            obj = json_decode(msg)
            self.bridge._on_message(obj)
        except:
            logging.info('Dropping corrupted message.')

    def close_handler(self):
        self.bridge.connected = False
        self.loop.stop()
        logging.error('Connection shutdown.')
        self.bridge.emit('disconnect')
        if self.bridge.reconnect:
            self.reconnect()

    def reconnect(self):
        logging.info('Attempting reconnect.')
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
            print(b'Connection.send: ' + buf)
        else:
            self.msg_queue.append(buf)
            print('Connection.send: (message queued).')
