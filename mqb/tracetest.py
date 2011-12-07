#!/usr/bin/env python

import sys
sys.path.append("..")

import puka


client = puka.Client("amqp://localhost/")
promise = client.connect()
client.wait(promise)

promise = client.queue_declare(queue='test2')
client.wait(promise)

print "  [*] Waiting for messages. Press CTRL+C to quit."

promise = client.queue_bind(exchange='amq.rabbitmq.trace', queue='test2',
                            routing_key='#')
print client.wait(promise)

consume_promise = client.basic_consume(queue='test2') # , prefetch_count=1)
while True:
    result = client.wait(consume_promise)
    print " [x] Received message %r" % (result,)
    client.basic_ack(result)

promise = client.close()
client.wait(promise)

