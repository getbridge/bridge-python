from mqblib import MQBConnection, waitForAll
import tornado
import json

class WrapRef(object):
    def __init__(self, owner, message):
        self.owner = owner
        self.target = message['from']
        self.objid = message['ref']
    
    def __call__(self, obj):
        self.owner.send_object(target=self.target, obj=obj)

class MQBAuthService(MQBConnection):
    public_name = "AUTH"
    def on_ready(self, result):
        self.log('SERVICE READY', result)
        self.bind_queue(queue=self.queue_name, exchange=self.DEFAULT_EXCHANGE, routing_key=self.public_name)
        self.bind_exchange(source=self.exchange_name, destination=self.USER_EXCHANGE)

    def on_message_received(self, message):
        self.log('message received', message)
        ref = WrapRef(self, message)
        ref(self)

def main():
    auth = MQBAuthService()
    auth.connect()

    ioloop = tornado.ioloop.IOLoop.instance()
    ioloop.start()

if __name__ == '__main__':
    main()