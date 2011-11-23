from mqblib import MQBConnection, waitForAll
import tornado

class MQBAuthService(MQBConnection):
    def on_ready(self, result):
        self.log('SERVICE READY', result)
        self.bind_queue(queue=self.queue_name, exchange=self.DEFAULT_EXCHANGE, routing_key="AUTH")

def main():
    auth = MQBAuthService()
    auth.connect()

    ioloop = tornado.ioloop.IOLoop.instance()
    ioloop.start()

if __name__ == '__main__':
    main()