# ***** BEGIN LICENSE BLOCK *****
#
# For copyright and licensing please refer to COPYING.
#
# ***** END LICENSE BLOCK *****

import json
import os
import sys

import pika

import tornado.ioloop

from pika.adapters.tornado_connection import TornadoConnection


class PikaClient(object):

    def __init__(self):
        # Construct a queue name we'll use for this instance only
        self.queue_name = 'COMMAND-QUEUE'
        self.exchange_name = 'COMMAND-EXCHANGE'


        # Default values
        self.connected = False
        self.connecting = False
        self.connection = None
        self.channel = None

        # A place for us to keep messages sent to us by Rabbitmq
        self.messages = list()

        # A place for us to put pending messages while we're waiting to connect
        self.pending = list()

    def connect(self):
        if self.connecting:
            pika.log.info('PikaClient: Already connecting to RabbitMQ')
            return
        pika.log.info('PikaClient: Connecting to RabbitMQ on localhost:5672')
        self.connecting = True

        credentials = pika.PlainCredentials('guest', 'guest')
        param = pika.ConnectionParameters(host='localhost',
                                          port=5672,
                                          virtual_host="/",
                                          credentials=credentials)
        self.connection = TornadoConnection(param,
                                            on_open_callback=self.on_connected)
        self.connection.add_on_close_callback(self.on_closed)

    def on_connected(self, connection):
        pika.log.info('PikaClient: Connected to RabbitMQ on localhost:5672')
        self.connected = True
        self.connection = connection
        self.connection.channel(self.on_channel_open)

    def on_channel_open(self, channel):
        pika.log.info('PikaClient: Channel Open, Declaring Default Exchange')
        self.channel = channel
        self.channel.exchange_declare(exchange='Default',
                                      type="topic",
                                      auto_delete=True,
                                      durable=False,
                                      callback=self.on_exchange_declared1)

    def on_exchange_declared1(self, frame):
        pika.log.info('PikaClient: Exchange1 Declared, Declaring Exchange2')
        self.channel.exchange_declare(exchange=self.exchange_name,
                                      type="fanout",
                                      auto_delete=True,
                                      durable=False,
                                      callback=self.on_exchange_declared2)

    def on_exchange_declared2(self, frame):
        pika.log.info('PikaClient: Exchanges Declared, Declaring Queue')
        self.channel.queue_declare(queue=self.queue_name,
                                   auto_delete=True,
                                   durable=False,
                                   exclusive=False,
                                   callback=self.on_queue_declared)

    def on_queue_declared(self, frame):
        pika.log.info('PikaClient: Queue Declared, Binding Queue')
        self.channel.queue_bind(exchange='Default',
                                queue=self.queue_name,
                                routing_key= self.queue_name + '.*',
                                callback=self.on_queue_bound1)

    def on_queue_bound1(self, frame):
        pika.log.info('PikaClient: Queue Bound, Binding Exchange %s to Default' % (self.exchange_name,))
        self.channel.exchange_bind(source=self.exchange_name, destination='Default', callback=self.on_queue_bound2 )

    def on_queue_bound2(self, frame):
        pika.log.info('PikaClient: Queue Bound2, Issuing Basic Consume')
        self.channel.basic_consume(consumer_callback=self.on_pika_message,
                                   queue=self.queue_name,
                                   no_ack=True)

        # # Send any messages pending
        # for properties, body in self.pending:
        #     self.channel.basic_publish(exchange='tornado',
        #                                routing_key='tornado.*',
        #                                body=body,
        #                                properties=properties)

    def on_pika_message(self, channel, method, header, body):
        print channel, method, header, body
        pika.log.info('PikaCient: Message receive, delivery tag #%i' % \
                     method.delivery_tag)
        # Append it to our messages list
        self.messages.append(body)

    def on_basic_cancel(self, frame):
        pika.log.info('PikaClient: Basic Cancel Ok')
        # If we don't have any more consumer processes running close
        self.connection.close()

    def on_closed(self, connection):
        # We've closed our pika connection so stop the demo
        tornado.ioloop.IOLoop.instance().stop()

    def sample_message(self, tornado_request):
        # Build a message to publish to RabbitMQ
        body = '%.8f: Request from %s [%s]' % \
               (tornado_request._start_time,
                tornado_request.remote_ip,
                tornado_request.headers.get("User-Agent"))

        # Send the message
        properties = pika.BasicProperties(content_type="text/plain",
                                          delivery_mode=1)
        self.channel.basic_publish(exchange='tornado',
                                   routing_key='tornado.*',
                                   body=body,
                                   properties=properties)

    def get_messages(self):
        # Get the messages to return, then empty the list
        output = self.messages
        self.messages = list()
        return output

if __name__ == '__main__':
    # Helper class PikaClient makes coding async Pika apps in tornado easy
    pc = PikaClient()
    # application.pika = pc  # We want a shortcut for below for easier typing

    # Set our pika.log options
    pika.log.setup(color=True)

    # Get a handle to the instance of IOLoop
    ioloop = tornado.ioloop.IOLoop.instance()

    # Add our Pika connect to the IOLoop since we loop on ioloop.start
    ioloop.add_timeout(1000, pc.connect)

    # Start the IOLoop
    ioloop.start()
