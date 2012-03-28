import sys
import json
import struct
import socket
import logging
from collections import deque
from datetime import timedelta

from tornado import ioloop, iostream
from tornado.escape import native_str
from tornado.httpclient import HTTPClient, HTTPError

from flotype import util, serializer, tcp


class Connection(object):
    def __init__(self, bridge):
        # Set associated bridge object
        self.bridge = bridge

        self.options = bridge._options

        # Preconnect buffer
        self.sock_buffer = SockBuffer()
        self.sock = self.sock_buffer
        
        # Create IO loop
        self.loop = ioloop.IOLoop.instance()
        
        # Connection configuration
        self.interval = 400
        self.client_id = None
        self.secret = None
        
    # Contact redirector for host and port
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
            body = util.parse(res.body).get('data')
        except:
            logging.error('Unable to parse redirector response %s', res.body)
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
            # Grow timeout for next reconnect attempt
            self.interval *= 2

    def establish_connection(self):
        logging.info('Starting TCP connection')
        # Set onmessage handler to handle CONNECT response
        self.onmessage = self.onconnectmessage
        tcp.Tcp(self)
  
    def onconnectmessage(self, message, sock):
        logging.info('Received clientId and secret')
        # Parse for client id and secret
        ids = message['data'].split('|')
        if len(ids) != 2:
            # Handle message normally if not a correct CONNECT response
            self.process_message(message, sock)
        else:
            self.client_id, self.secret = ids
            # Reset reconnect interval
            self.interval = 400
            # Send preconnect queued messages
            self.sock.process_queue(sock, self.client_id)
            # Set connection socket to connected socket
            self.sock = sock
            # Set onmessage handler to handle standard messages
            self.onmessage = self.process_message
            logging.info('Handshake complete')
            # Trigger ready callback
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
        # Convert serialized ref objects to callable references
        serializer.unserialize(self.bridge, obj)
        # Extract RPC destination address
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
        sock.send(native_str(msg))
   
    def onclose(self):
        logging.error('Connection closed')
        # Restore preconnect buffer as socket connection
        self.sock = self.sock_buffer
        if self.options['reconnect']:
            self.reconnect()

    def send_command(self, command, data):
        msg = util.stringify({'command': command, 'data': data})
        logging.info('Sending %s', msg)
        self.sock.send(native_str(msg))

    def start(self):
        if not (self.options.get('host') and self.options.get('port')):
            self.redirector()
        else:
            # Host and port are specified
            self.establish_connection()
        self.loop.start()

class SockBuffer (object):
    def __init__(self):
        # Buffer for preconnect messages
        self.buffer = deque()
        
    def send(self, msg):
        self.buffer.append(native_str(msg))
        
    def process_queue(self, sock, client_id):
        while len(self.buffer):
            # Replace null client ids with actual client_id after handshake
            sock.send(self.buffer.popleft().replace('"client", null', '"client", "' + client_id + '"'))
        self.buffer = deque()
        
