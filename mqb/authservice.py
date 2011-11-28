from mqblib import MQBConnection, waitForAll
import tornado
import json

from seria import NowObject, NowClient

import functools 

from helpers import waitForAll

class MQBService(MQBConnection):
    def on_ready(self, result):
        self.log('ON READY', result)

        self.empty_register()

        self.now = NowClient(exchange=self)
        self.auth = AuthService(self.now, name='auth')

class AuthService(NowObject):
    def handle_login(self, username, password, callback):
        print 'LALALA'

        print 'CALLBACK', callback
        callback('FRED')

def main():
    mqb = MQBService(client_id='SERVER')
    mqb.connect()

    def done(register_name):
        print 'DONE', register_name
    mqb.register('auth', done)

    ioloop = tornado.ioloop.IOLoop.instance()
    ioloop.start()

if __name__ == '__main__':
    main()