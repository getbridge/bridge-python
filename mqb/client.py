from mqblib import MQBConnection, waitForAll
import tornado

class MQBClient(MQBConnection):
    def on_ready(self, result):
        self.log('SERVICE READY', result)
        self.publish(exchange=self.DEFAULT_EXCHANGE, body="Hello world!", routing_key='AUTH')

def main():
    client = MQBClient()
    client.connect()

    ioloop = tornado.ioloop.IOLoop.instance()
    ioloop.start()

if __name__ == '__main__':
    main()