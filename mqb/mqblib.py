import puka
import tornado.ioloop

from helpers import AttrDict, waitForAll

import functools, uuid
DEFAULT_EXCHANGE = 'DEFAULT'

class TornadoDriver(object):
    def connect(self, config, callback):
        ioloop = tornado.ioloop.IOLoop.instance()

        self.connection = puka.Client("amqp://%s:%s@%s:%s/%s" % (config.username, config.password, config.host, config.port, config.vhost))
        self.connection.connect(callback=callback)

        ioloop.add_handler(self.connection.fileno(), self.ioloop_triggered, 0)
        self.update_conn()
        return self.connection

    def ioloop_triggered(self, fd, events):
        ioloop = tornado.ioloop.IOLoop.instance()
        if events & ioloop.READ:
            self.connection.on_read()
        if events & ioloop.WRITE:
            self.connection.on_write()
        self.update_conn()

    def update_conn(self):
        ioloop = tornado.ioloop.IOLoop.instance()
        state = ioloop.READ
        if self.connection.needs_write():
            state |= ioloop.WRITE
        
        ioloop.update_handler(self.connection.fileno(), state)
        self.connection.run_any_callbacks()

class MQBConnection(object):
    def __init__(self, **kwargs):
        defaults = {
            'host': 'localhost',
            'port': 5672,
            'vhost': '',
            'client_id': None,
            'username': 'guest',
            'password': 'guest',
        }
        self.connection = None

        self.config = AttrDict(defaults)
        self.config.update(**kwargs)

        self.config['client_id'] = self.config.client_id or uuid.uuid4().hex

    def log(self, arg):
        print self.config.client_id + ': ' + arg

    def connect(self):
        def done(*args):
            print 'hello', args

        self.connection = TornadoDriver().connect(self.config, done)

def main():
    command = MQBConnection()
    command.connect()

    ioloop = tornado.ioloop.IOLoop.instance()
    ioloop.start()

if __name__ == '__main__':
    main()