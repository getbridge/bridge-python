from mqblib import MQBConnection, waitForAll
import tornado

from seria import NowObject, NowClient

import json

class MyNow(NowClient):
    def handle_logged_in(self, lala):
        print 'LOGGED IN', lala

class MQBClient(MQBConnection):
    def on_ready(self, result):
        self.log('CLIENT READY', result)

        self.now = MyNow(name='CLIENT',exchange=self)
        self.now.auth.login(username='enki', password='secret', callback=self.now.logged_in)
    
    
def main():
    mqb = MQBClient(client_id='CLIENT')
    mqb.connect()

    now = NowClient(exchange=mqb)
    # now.auth.login()

    ioloop = tornado.ioloop.IOLoop.instance()
    ioloop.start()

if __name__ == '__main__':
    main()