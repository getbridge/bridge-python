import sys
import struct
import socket

from tornado import iostream
from tornado.escape import utf8, native_str

class Tcp(object):
    def __init__(self, connection):
        self.connection = connection
        # Start socket
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        # Create IOStream for TCP connection
        self.stream = iostream.IOStream(self.socket)
        server = (self.connection.options['host'], self.connection.options['port'])
        self.stream.connect(server, self.onopen)
        self.stream.set_close_callback(self.connection.onclose)

    def onopen(self):
        self.connection.onopen(self)
        self.wait()
    
    def wait(self):
        # Read header bytes
        self.stream.read_bytes(4, self.header_handler)

    def header_handler(self, data):
        size = struct.unpack('>I', data)[0]
        # Read body bytes
        self.stream.read_bytes(size, self.body_handler)

    def body_handler(self, data):
        # Call message handler
        self.connection.onmessage({'data': native_str(data)}, self)
        # Await next message
        self.wait()

    def send(self, arg):
        arg = utf8(arg)
        # Prepend length header to message
        self.stream.write(struct.pack('>I', len(arg)) + arg)

