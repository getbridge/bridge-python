import puka
import uuid
import traceback
import tornado.ioloop

from helpers import AttrDict, waitForAll
import functools, json

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
        'P': 'path',
        'F': 'fanout',
        'T': 'topic',
    }
    DEFAULT_EXCHANGE = 'D_DEFAULT'

    def __init__(self, **kwargs):
        self.want_register = []
        self.connected = False
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

        assert self.config.client_id
    
    # def register(self, name, callback=None):
    #     self.want_register.append( (name, callback) )
    #     if self.connected:
    #         self.empty_register()

    # def empty_register(self):
    #     while self.want_register:
    #         self.register_1( *self.want_register.pop(0) )

    # def register_1(self, register_name, callback):
    #     waitForAll(functools.partial(self.register_2, register_name, callback), {
    #             'declare': [self.declare_queue, [], dict(queue=register_name)],
    #         }
    #     )
    
    # def register_2(self, register_name, callback, result):
    #     self.listen(queue=register_name)
    #     waitForAll(functools.partial(self.register_3, register_name, callback), {
    #         'bindq': [self.bind_queue, [], dict(queue=register_name, exchange=self.DEFAULT_EXCHANGE, routing_key=register_name)]
    #         }
    #     )

    # def register_3(self, register_name, callback, result):
    #     self.log('BOUND READY', result)

    #     # self.publish(exchange=self.exchange_name, body='hello', routing_key='auth')

    #     if callback:
    #         callback(register_name)

    def log(self, *args):
        print self.config.client_id + ': ' + ' '.join( str(x) for x in args)

    def connect(self, callback):
        self.callback = callback
        self.client = TornadoDriver().connect(self.config, self.connection_made, self.connection_lost)
    
    def connection_made(self, promise, result):
        # self.log('Connected to %s' %(result,))

        self.connected = True

        d = self.setup_base()
        waitForAll(self.have_client_queue_and_exchange, d )

    def connection_lost(self, exception):
        self.log('connection lost', exception)

    def have_client_queue_and_exchange(self, result):
        # print 'ALMOST LISTENING', result
        self.listen_client()
        waitForAll(lambda x: self.callback(), self.link_client())

    @property
    def queue_name(self):
        return 'C_' + self.config.client_id

    @property
    def exchange_name(self):
        return 'T_' + self.config.client_id

    def declare_exchange(self, exchange=None, *args, **kwargs):
        typ = self.EXCHANGE_TYPE_MAP[ exchange[0] ]
        return self.client.exchange_declare( exchange=exchange, type=typ, durable=False, auto_delete=False, *args, **kwargs)

    def declare_queue(self, queue=None, *args, **kwargs):
        return self.client.queue_declare(queue=queue, durable=False, auto_delete=True, *args, **kwargs)

    def bind_queue(self, *args, **kwargs):
        print 'BINDQUEUE', args, kwargs
        return self.client.queue_bind(*args, **kwargs)
    
    def bind_exchange(self, *args, **kwargs):
        print 'BINDEXCHANGE', args, kwargs
        return self.client.exchange_bind(*args, **kwargs)

    def publish(self, *args, **kwargs):
        return self.client.basic_publish(*args, **kwargs)

    def setup_base(self):
        return {
            'default_exchange': [self.declare_exchange, [], dict(exchange=self.DEFAULT_EXCHANGE)],
            'client_queue': [self.declare_queue, [], dict(queue=self.queue_name)],
            'client_exchange': [self.declare_exchange, [], dict(exchange=self.exchange_name)],
        }
    
    def on_datagram_received(self, promise, datagram):
        print 'datagram received', datagram
        all_links = []
        for key, value in datagram['headers'].items():
            if not key.startswith('link_'):
                continue
            all_links.append([self.bind_queue, [], dict(exchange=self.exchange_name, queue='C_' + value, routing_key=value)])

        waitForAll( functools.partial(self.links_made, datagram), all_links)
    
    def links_made(self, datagram, *args, **kwargs):
        packet = json.loads(datagram['body'])
        serargskwargs = packet['serargskwargs']
        pathchain = packet['pathchain']
        self.message_received(pathchain, serargskwargs)

    def send(self, routing_key, is_namespaced, pathchain, serargskwargs, add_links, callback=None):
        # print 'IS NAMESPACED', is_namespaced, pathchain
        if is_namespaced:
            routing_key = 'N.' + routing_key
        data = dict(exchange=self.exchange_name, routing_key=routing_key, body=json.dumps({'pathchain': pathchain, 'serargskwargs': serargskwargs}))
        print 'SEND', data
        if callback:
            data['callback'] = callback
        data['headers'] = dict((('link_%d' % (pos,)), x) for (pos, x) in enumerate(add_links) )
        return self.publish(**data)

    def listen_client(self):
        self.listen(self.queue_name)

    def listen(self, queue):
        self.client.basic_consume(queue=queue, callback=self.on_datagram_received, ) #consumer_tag=self.queue_name + ':' + uuid.uuid4().hex )

    def link_client(self):
        return { 
            'exchange_bind': [self.bind_exchange, [], dict(source=self.exchange_name, destination=self.DEFAULT_EXCHANGE, routing_key='N.*')],
        }


def main():
    command = MQBConnection()
    command.connect()

    ioloop = tornado.ioloop.IOLoop.instance()
    ioloop.start()

if __name__ == '__main__':
    main()