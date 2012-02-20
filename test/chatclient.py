#!/usr/bin/python

import logging
from bridge import Bridge, Service

bridge = Bridge(log_level=logging.DEBUG)

class MsgHandler(Service):
    def msg(self, name, message):
        print(name + ': ' + message)

def start_client():
    bridge.get_service('chatserver', start_chat)

def start_chat(chat):
    print('Got chat service = ', chat)
    chat.join('lobby', MsgHandler(), get_channel)

lobby = None

def get_channel(channel):
    lobby = channel

def send(message):
    lobby.msg('Foo', message)

bridge.ready(start_client)
