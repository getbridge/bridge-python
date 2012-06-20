import sys
import struct
import socket
import ssl

from tornado import iostream
from tornado.escape import utf8, native_str

from BridgePython import data
import os.path

class Tcp(object):
    def __init__(self, connection):
        self.connection = connection
        # Start socket
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        if connection.options["secure"]:
            cert_dir = os.path.split(data.__file__)[0]
            cert_file = os.path.join(cert_dir, "BridgePythoncrt")
            ssl.wrap_socket(self.socket, cert_reqs=ssl.CERT_REQUIRED, \
                    ca_certs=cert_file)
            # Use SSL IO Stream for secure connection
            self.stream = iostream.SSLIOStream(self.socket)
        else:
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

