#!/usr/bin/python

import logging
from bridge import Bridge 

bridge = Bridge(host='localhost', port=8090, log_level=logging.DEBUG, api_key='qwertyui', reconnect=False)

class MsgHandler(object):
    def msg(self, name, message):
        print(name + ': ' + message)

class LobbyHandler(object):
    def __init__(self, name):
        self.name = name
        self.lobby = None

    def __call__(self, channel, name):
        self.lobby = channel
        self.send('Hello, world.')

    def send(self, message):
        self.lobby.msg(self.name, message)

def start_client():
    lobby = LobbyHandler('Vedant')
    chat = bridge.get_service('chatserver')
    chat.join('lobby', MsgHandler, lobby)

bridge.ready(start_client)
