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

from flotype import util, serializer, tcp


class Connection(object):
    def __init__(self, bridge):
        # Set associated bridge object.
        self.bridge = bridge

        # Set options.
        self.options = bridge._options

        # Preconnect buffer
        self.sock_buffer = SockBuffer()
        self.sock = self.sock_buffer
        
        self.loop = ioloop.IOLoop.instance()
        
        # Connection configuration.
        self.interval = 400
        
        self.client_id = None
        self.secret = None
        
        
    def redirector(self):
        client = HTTPClient()
        try:
            res = client.fetch('%s/redirect/%s' % (
                self.options['redirector'], self.options['api_key']
            ))
        except:
            logging.error('Unable to contact redirector')
            client.close()
            return

        try:
            body = json.loads(res.body).get('data')
        except:
            logging.error('Unable to parse redirector response %s', res.body)
            client.close()
            return

        if not ('bridge_port' in body and 'bridge_host' in body):
            logging.error('Could not find host and port in JSON body')
        else:
            self.options['host'] = body.get('bridge_host')
            self.options['port'] = int(body.get('bridge_port'))
            self.establish_connection()
        client.close()

    def reconnect(self):
        logging.info('Attempting reconnect')
        if self.interval < 32678:
            delta = timedelta(milliseconds=self.interval)
            self.loop.add_timeout(delta, self.establish_connection)
            self.interval *= 2

    def establish_connection(self):
        logging.info('Starting TCP connection %s, %s', self.options['host'], self.options['port'])
        self.onmessage = self.onconnectmessage
        tcp.Tcp(self)
  
    def onconnectmessage(self, message, sock):
        ids = message['data'].split('|')
        if len(ids) != 2:
            self.process_message(message, sock)
        else:
            logging.info('client_id received, %s', ids[0])
            self.client_id, self.secret = ids
            self.sock.process_queue(sock, self.client_id)
            self.sock = sock
            self.onmessage = self.process_message
            logging.info('Handshake complete')
            if not self.bridge._ready:
              self.bridge._ready = True
              self.bridge.emit('ready')

    def process_message(self, message, sock):
        logging.info('Received %s', message['data'])
        try:
            obj = util.parse(message['data'])
        except:
            logging.warn('Message parsing failed')
            return
        serializer.unserialize(self.bridge, obj)
        destination = obj.get('destination', None)
        if not destination:
            logging.warn('No destination in message')
            return
        self.bridge._execute(destination._address, obj['args'])
   
    def onopen(self, sock):
        logging.info('Beginning handshake')
        msg = util.stringify({
            'command': 'CONNECT',
            'data': {
                'session': [self.client_id, self.secret],
                'api_key': self.options['api_key'],
            }
        })
        sock.send(msg)
   
    def onclose(self):
        logging.error('Connection closed')
        self.sock = self.sock_buffer
        if self.options['reconnect']:
            self.reconnect()

    def send_command(self, command, data):
        msg = util.stringify({'command': command, 'data': data})
        logging.info('Sending %s', msg)
        self.sock.send(msg)

    def start(self):
        if not (self.options.get('host') and self.options.get('port')):
            self.redirector()
        else:
            self.establish_connection()
        self.loop.start()

class SockBuffer (object):
    def __init__(self):
        self.buffer = deque()
        
    def send(self, msg):
        self.buffer.append(msg)
        
    def process_queue(self, sock, client_id):
        while len(self.buffer):
            sock.send(self.buffer.popleft().replace('"client", null', '"client", "' + client_id + '"'))
        self.buffer = deque()
        