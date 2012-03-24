import sys
import json
import struct
import socket
import logging
from collections import deque
from datetime import timedelta

from tornado import ioloop, iostream
from tornado.escape import utf8, to_unicode
from tornado.httpclient import HTTPClient, HTTPError

from flotype import util


class Connection(object):
    def __init__(self, bridge, interval=400):
        # Set associated bridge object.
        self.bridge = bridge

        # Set options.
        self.options = bridge._options

        # Connection configuration.
        self.interval = interval
        self.loop = ioloop.IOLoop.instance()
        self.msg_queue = deque()
        self.on_message = self._connect_on_message

        # Client identification.
        self.client_id = None
        self.id_promise = util.Promise(self, 'client_id')
        self.secret = None

        if not (self.options.get('host') and self.options.get('port')):
            self.redirector()
        else:
            self.establish_connection()

    def redirector(self):
        client = HTTPClient()
        try:
            res = client.fetch('%s/redirect/%s' % (
                self.options['redirector'], self.options['api_key']
            ))
        except:
            logging.error('Unable to contact redirector.')
            client.close()
            return

        try:
            body = json.loads(res.body).get('data')
        except:
            logging.error('Unable to parse redirector response %s.', res.body)
            client.close()
            return

        if not ('bridge_port' in body and 'bridge_host' in body):
            logging.error('Could not find host and port in JSON body.')
        else:
            self.options['host'] = body.get('bridge_host')
            self.options['port'] = int(body.get('bridge_port'))
            self.establish_connection()
        client.close()

    def reconnect(self):
        self.on_message = self._connect_on_message
        if self.interval < 32678:
            delta = timedelta(milliseconds=self.interval)
            self.loop.add_timeout(delta, self.establish_connection)

    def establish_connection(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.stream = iostream.IOStream(self.sock)
        logging.info('Starting TCP connection.')
        server = (self.options['host'], self.options['port'])
        self.stream.connect(server, self.on_connect)

    def on_connect(self):
        logging.info('Beginning handshake.')
        msg = {
            'command': 'CONNECT',
            'data': {
                'session': [self.client_id, self.secret],
                'api_key': self.options['api_key'],
            },
        }
        self._send_noqueue(msg)
        self.stream.set_close_callback(self.on_close)
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
        logging.info('Received clientId and secret.')
        ids = msg.split('|')
        if len(ids) != 2:
            self._process_message(msg)
        else:
            self.client_id, self.secret = ids
            self.on_message = self._process_message
            self.process_queue()
            self.bridge._on_ready()
            
    def _process_message(self, msg):
        try:
            obj = json.loads(msg)
        except:
            logging.warn('Could not parse message from server.')
            return

        logging.debug('Received %s', msg)
        util.deserialize(self.bridge, obj)
        destination = obj.get('destination', None)
        if not destination:
            logging.warn('No destination in message.')
            return

        self.bridge._execute(destination._address, obj['args'])

    def on_close(self):
        logging.error('Connection closed.')
        self.bridge._ready = False
        self.bridge.emit('disconnect')
        if self.options['reconnect']:
            self.reconnect()

    def process_queue(self):
        while len(self.msg_queue) and self.bridge._ready:
            msg = self.msg_queue.popleft()
            self._send_noqueue(msg)

    def send_command(self, command, data):
        msg = {
            'command': command,
            'data': data,
        }
        msg = util.serialize(self.bridge, msg)
        self.send(msg)

    def send(self, msg):
        if self.bridge._ready:
            self._send_noqueue(msg)
        else:
            self.msg_queue.append(msg)

    def _send_noqueue(self, msg):
        self._send(utf8(json.dumps(msg, default=str)))

    def _send(self, data):
        size = struct.pack('>I', len(data))
        buf = size + data
        self.stream.write(buf)

    def start(self):
        self.loop.start()
