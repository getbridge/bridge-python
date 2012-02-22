#!/usr/bin/python

import logging
from bridge import Bridge 

bridge = Bridge(log_level=logging.DEBUG)

class MsgHandler(object):
    def msg(self, name, message):
        print(name + ': ' + message)

class LobbyHandler(object):
    def __init__(self, name):
        self.name = name
        self.lobby = None

    def __call__(self, channel):
        print("==> LobbyHandler:", args)
        self.lobby = channel # args[0]
        self.send('Hello, world.')

    def send(self, message):
        self.lobby.msg(self.name, message)

lobby = LobbyHandler('Vedant')

def start_client():
    bridge.get_service('chatserver', start_chat)

def start_chat(chat):
    print('Got chat service.')
    chat.join('lobby', MsgHandler, lobby)

bridge.ready(start_client)
