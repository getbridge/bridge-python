import sys
import struct
import socket
import logging
from collections import deque
from datetime import timedelta

from tornado import ioloop, iostream
from tornado.escape import json_encode, json_decode, utf8, to_unicode
from tornado.httpclient import HTTPClient, HTTPError


class Connection(object):
    def __init__(self, bridge, interval=400):

        # Set associated bridge object
        self.bridge = bridge

        self.options = bridge._options

        # Connection configurations
        self.interval = interval
        self.loop = ioloop.IOLoop.instance()
        self.msg_queue = deque()
        self.on_message = self._connect_on_message

        self.client_id = None
        self.secret = None

        if self.options.get('host') is not None
        and self.options.get('port') is not None:
            self.redirector()
        else:
            self.establish_connection()

    def redirector(self):
        client = HTTPClient()
        logging.info('Contacting redirector...')
        try:
            res = client.fetch('%sredirect/%s' % (
                self.bridge.redirector, self.bridge.api_key
            ))
            body = json_decode(res.body).get('data')
            if('bridge_port' not in body or 'bridge_host' not in body):
                logging.error('Could not find host and port in JSON')
            else:
                self.options.host = body.get('bridge_host')
                self.options.port = int(body.get('bridge_port'))
                self.establish_connection()
            client.close()
        except:
            logging.error('Could not resolve host with redirector.')
            client.close()
            return

    def reconnect(self):
        self.on_message = self._connect_on_message
        if not self.connected and self.interval < 32678:
            delta = timedelta(milliseconds=self.interval)
            self.loop.add_timeout(delta, self.establish_connection)

    def establish_connection(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.stream = iostream.IOStream(self.sock)
        logging.info('Starting TCP connection')
        server = (self.options.host, self.options.port)
        self.stream.connect(server, self.on_connect)
        if not self.loop.running():
            self.loop.start()

    def on_connect(self):
        logging.info('Beginning handshake')
        msg = {
            'command': 'CONNECT',
            'data': {
                'session': [self.client_id, self.secret],
                'api_key': self.bridge.api_key,
            },
        }
        self.send(msg)
        self.stream.set_close_callback(self.on_close)
        if len(self.msg_queue):
            self.bridge.emit('reconnect')
            self.loop.add_callback(self.process_queue)
        self.wait()

    def wait(self):
        self.stream.read_bytes(4, self.header_handler)

    def header_handler(self, data):
        size = struct.unpack('>I', data)[0]
        self.stream.read_bytes(size, self.body_handler)

    def body_handler(self, data):
        self.on_message(to_unicode(data))
        self.wait()

    def _connect_on_message(self, msg):
        logging.info('clientId and secret received')
        try:
            self.client_id, self.secret = msg.split('|')
            self.on_message = self._json_on_message
            self.bridge._on_ready()
        except:
            return

    def _json_on_message(self, msg):
        try:
            obj = json_decode(msg)
            logging.info('Received %s', msg)
            self.bridge._on_message(obj)
        except:
            logging.info('Message parsing failed')

    def on_close(self):
        self.bridge.connected = False
        logging.error('Connection closed')
        self.bridge.emit('disconnect')
        if self.options.reconnect:
            self.reconnect()

    def process_queue(self):
        while self.bridge.connected and len(self.msg_queue):
            buf = self.msg_queue.popleft()
            self.stream.write(buf)

    def send_command(self, command, data):
        msg = {'command': command, 'data': data}
        msg = util.serialize(self.bridge, msg)
        self.send(msg)

    def send(self, msg):
        data = utf8(json_encode(msg))
        size = struct.pack('>I', len(data))
        buf = size + data
        if self.bridge.connected:
            self.stream.write(buf)
        else:
            self.msg_queue.append(buf)
