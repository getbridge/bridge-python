from mqblib import MQBConnection, waitForAll
import tornado
import json

from seria import NowObject, NowClient

from helpers import waitForAll

class MQBService(MQBConnection):
    # public_name = "auth"
    def on_ready(self, result):
        self.log('ON READY', result)

        waitForAll(self.declared_auth, {
                'declare': [self.declare_queue, [], dict(queue='auth')],
                'bind': [self.bind_exchange, [], dict(source=self.exchange_name, destination=self.USER_EXCHANGE)],
            }
        )
    
    def declared_auth(self, result):
        self.log('DECLARED AUTH', result)
        waitForAll(self.bound, {
            'bindq': [self.bind_queue, [], dict(queue='auth', exchange=self.DEFAULT_EXCHANGE, routing_key='auth')]
            }
        )
        self.client.basic_consume(queue='auth', callback=self.on_datagram_received)

    def bound(self, result):
        self.log('BOUND READY', result)

        self.send_object(target='auth', obj='hello')

    def on_datagram_received(self, promise, datagram):
        self.log('datagram received', datagram)

class AuthService(NowClient):
    pass

def main():
    service = MQBService()
    service.connect()

    ioloop = tornado.ioloop.IOLoop.instance()
    ioloop.start()

if __name__ == '__main__':
    main()