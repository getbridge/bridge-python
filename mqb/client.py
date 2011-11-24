from mqblib import MQBConnection, waitForAll
import tornado

import json

class MQBClient(MQBConnection):
    def on_ready(self, result):
        self.log('SERVICE READY', result)
        self.get_auth_ref()
    
    def auth_received(self, authref):
        print 'AUTH ref', authref

    def on_message_received(self, message):
        print 'message received', message

    def get_auth_ref(self):
        self.send_object(target='AUTH', obj=self.auth_received)

def main():
    client = MQBClient()
    client.connect()

    ioloop = tornado.ioloop.IOLoop.instance()
    ioloop.start()

if __name__ == '__main__':
    main()