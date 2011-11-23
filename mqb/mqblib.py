import puka
import traceback
import tornado.ioloop

from helpers import AttrDict, waitForAll

import uuid
DEFAULT_EXCHANGE = 'DEFAULT'
USER_EXCHANGE = 'USER'


class TornadoDriver(object):
    def connect(self, config, open_callback, close_callback):
        ioloop = tornado.ioloop.IOLoop.instance()

        self.connection = puka.Client("amqp://%s:%s@%s:%s/%s" % (config.username, config.password, config.host, config.port, config.vhost))
        self.connection.connect(callback=open_callback)
        self.close_callback = close_callback

        ioloop.add_handler(self.connection.fileno(), self.ioloop_triggered, 0)
        self.update_conn()
        return self.connection

    def ioloop_triggered(self, fd, events):
        ioloop = tornado.ioloop.IOLoop.instance()
        try:
            if events & ioloop.READ:
                self.connection.on_read()
            if events & ioloop.WRITE:
                self.connection.on_write()
            self.update_conn()
        except Exception, e:
            traceback.print_exc()
            ioloop.remove_handler(fd)
            self.close_callback(e)

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
        self.client = None

        self.config = AttrDict(defaults)
        self.config.update(**kwargs)

        self.config['client_id'] = self.config.client_id or uuid.uuid4().hex

    def log(self, arg):
        print self.config.client_id + ': ' + arg

    def connect(self):
        self.client = TornadoDriver().connect(self.config, self.connection_made, self.connection_lost)
    
    def connection_made(self, promise, result):
        self.log('Connected to %s' %(result,))

        d = self.setup_base()
        d.update( self.setup_client() )
        waitForAll(self.setup_done, d )

    def connection_lost(self, exception):
        print 'connection lost', exception

    def setup_done(self, result):
        print 'setup_done', result
        self.listen_client()
        waitForAll(self.linked_in, self.link_client())

    def linked_in(self, result):
        print 'linked_in', result
        promise = self.client.basic_publish(exchange=USER_EXCHANGE, body="Hello world!")
        foo = self.client.wait(promise)
        print 'published', foo, promise

    @property
    def queue_name(self):
        return 'I_' + self.config.client_id

    @property
    def exchange_name(self):
        return 'O_' + self.config.client_id

    def setup_base(self):
        return {
            'default_exchange': [self.client.exchange_declare, [], dict(exchange=DEFAULT_EXCHANGE, type='fanout', durable=False, auto_delete=False)],
            'user_exchange': [self.client.exchange_declare, [], dict(exchange=USER_EXCHANGE, type='fanout', durable=False, auto_delete=False)],
        }

    def setup_client(self):
        return {
            'client_queue': [self.client.queue_declare, [], dict(queue=self.queue_name, durable=False, auto_delete=True)],
            'client_exchange': [self.client.exchange_declare, [], dict(exchange=self.exchange_name, type='fanout', durable=False, auto_delete=False)],
        }
    
    def on_basic_consume(self, *args, **kwargs):
        print 'basic consume callback', args, kwargs

    def listen_client(self):
        self.client.basic_consume(queue=self.queue_name, callback=self.on_basic_consume)

    def link_client(self):
        return { 
                'queue_bind': [self.client.queue_bind, [], dict(queue=self.queue_name, exchange=USER_EXCHANGE, routing_key=self.queue_name)],
                'exchange_bind': [self.client.exchange_bind, [], dict(source=self.exchange_name, destination=DEFAULT_EXCHANGE, routing_key=self.queue_name)]
               }


def main():
    command = MQBConnection()
    command.connect()

    ioloop = tornado.ioloop.IOLoop.instance()
    ioloop.start()

if __name__ == '__main__':
    main()