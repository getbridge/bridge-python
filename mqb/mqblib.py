import puka
import traceback
import tornado.ioloop

from helpers import AttrDict, waitForAll

import uuid

class TornadoDriver(object):
    def connect(self, config, open_callback, close_callback):
        ioloop = tornado.ioloop.IOLoop.instance()

        self.client = puka.Client("amqp://%s:%s@%s:%s/%s" % (config.username, config.password, config.host, config.port, config.vhost))
        self.client.connect(callback=open_callback)
        self.close_callback = close_callback

        ioloop.add_handler(self.client.fileno(), self.ioloop_triggered, 0)
        self.update_conn()
        return self.client

    def ioloop_triggered(self, fd, events):
        ioloop = tornado.ioloop.IOLoop.instance()
        try:
            if events & ioloop.READ:
                self.client.on_read()
            if events & ioloop.WRITE:
                self.client.on_write()
            self.update_conn()
        except Exception, e:
            traceback.print_exc()
            ioloop.remove_handler(fd)
            self.close_callback(e)

    def update_conn(self):
        self.client.run_any_callbacks()
        ioloop = tornado.ioloop.IOLoop.instance()
        state = ioloop.READ
        if self.client.needs_write():
            state |= ioloop.WRITE
        
        ioloop.update_handler(self.client.fileno(), state)

class MQBConnection(object):
    EXCHANGE_TYPE_MAP = {
        'D': 'direct',
        'F': 'fanout',
        'T': 'topic',
    }
    DEFAULT_EXCHANGE = 'D_DEFAULT'
    USER_EXCHANGE = 'D_USER'

    def __init__(self, **kwargs):
        defaults = {
            'host': 'localhost',
            'port': 5672,
            'vhost': '',
            'client_id': None,
            'username': 'guest',
            'password': 'guest',
        }
        self.client = None

        self.config = AttrDict(defaults)
        self.config.update(**kwargs)

        self.config['client_id'] = self.config.client_id or uuid.uuid4().hex

    def log(self, *args):
        print self.config.client_id + ': ' + ' '.join( str(x) for x in args)

    def connect(self):
        self.client = TornadoDriver().connect(self.config, self.connection_made, self.connection_lost)
    
    def connection_made(self, promise, result):
        # self.log('Connected to %s' %(result,))

        d = self.setup_base()
        d.update( self.setup_client_queue_and_exchange() )
        waitForAll(self.have_client_queue_and_exchange, d )

    def connection_lost(self, exception):
        self.log('connection lost', exception)

    def have_client_queue_and_exchange(self, result):
        print result
        self.listen_client()
        waitForAll(self.on_ready, self.link_client())

    def on_ready(self, result):
        raise NotImplementedError

    @property
    def queue_name(self):
        return self.config.client_id

    @property
    def exchange_name(self):
        return 'F_' + self.config.client_id

    def declare_exchange(self, exchange=None, *args, **kwargs):
        typ = self.EXCHANGE_TYPE_MAP[ exchange[0] ]
        return self.client.exchange_declare( exchange=exchange, type=typ, durable=False, auto_delete=False, *args, **kwargs)

    def declare_queue(self, queue=None, *args, **kwargs):
        return self.client.queue_declare(queue=self.queue_name, durable=False, auto_delete=True, *args, **kwargs)

    def bind_queue(self, *args, **kwargs):
        return self.client.queue_bind(*args, **kwargs)
    
    def bind_exchange(self, *args, **kwargs):
        return self.client.exchange_bind(*args, **kwargs)

    def publish(self, *args, **kwargs):
        return self.client.basic_publish(*args, **kwargs)

    def setup_base(self):
        return {
            'default_exchange': [self.declare_exchange, [], dict(exchange=self.DEFAULT_EXCHANGE)],
            'user_exchange': [self.declare_exchange, [], dict(exchange=self.USER_EXCHANGE)],
        }

    def setup_client_queue_and_exchange(self):
        return {
            'client_queue': [self.declare_queue, [], dict(queue=self.queue_name)],
            'client_exchange': [self.declare_exchange, [], dict(exchange=self.exchange_name)],
        }
    
    def on_basic_consume(self, *args, **kwargs):
        self.log('basic consume callback', args, kwargs)

    def listen_client(self):
        self.client.basic_consume(queue=self.queue_name, callback=self.on_basic_consume)

    def link_client(self):
        return { 
                'queue_bind': [self.bind_queue, [], dict(queue=self.queue_name, exchange=self.USER_EXCHANGE, routing_key=self.queue_name)],
                'exchange_bind': [self.bind_exchange, [], dict(source=self.exchange_name, destination=self.DEFAULT_EXCHANGE)]
               }


def main():
    command = MQBConnection()
    command.connect()

    ioloop = tornado.ioloop.IOLoop.instance()
    ioloop.start()

if __name__ == '__main__':
    main()