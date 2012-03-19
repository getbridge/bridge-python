#!/usr/bin/python

import logging
from flotype.bridge import Bridge

bridge = Bridge(host='localhost', port=8090, log_level=logging.DEBUG,
        api_key='abcdefgh', reconnect=True)


class Handler(bridge.Service):
    def someFn(self, name, message):
        print(name + ': ' + message)


def callback(message):
    self.lobby.msg(self.name, message)


def start_client():
    handler = Handler()

    someService = bridge.get_service('someService')
    someService.someFn(1, 1.0, 'foo', True, None, ['foo', 'bar'], {'foo': 'bar'})
    someService.someFn(handler, callback);

    someChannel = bridge.get_channel('someChannel')
    someChannel.someFn(1, 1.0, 'foo', True, None, ['foo', 'bar'], {'foo': 'bar'})

    bridge.join_channel('myChannel', handler, callback)
    bridge.join_channel('myChannel', handler)

    bridge.publish_service('myService', handler, callback)
    bridge.publish_service('myService', handler)

    bridge.leave_channel('myChannel', handler)
    bridge.leave_channel('myChannel', handler, callback)

bridge.ready(start_client)
bridge.connect()
