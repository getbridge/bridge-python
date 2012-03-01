#!/usr/bin/python

import logging
from bridge import Bridge 

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
    someService.someFn(1, 1.0, 'foo', True, None, ['foo', 'bar'], {'foo' : 'bar'})
    someService.someFn(handler, callback);

bridge.ready(start_client)
