from mqblib import MQBConnection, waitForAll
import tornado

from seria import NowObject, NowClient

import json

class MQBClient(MQBConnection):
    def on_ready(self, result):
        self.log('CLIENT READY', result)

        self.now = NowClient(exchange=self)
        self.now.auth.login()
    
def main():
    mqb = MQBClient(client_id='CLIENT')
    mqb.connect()

    now = NowClient(exchange=mqb)
    # now.auth.login()

    ioloop = tornado.ioloop.IOLoop.instance()
    ioloop.start()

if __name__ == '__main__':
    main()