#!/usr/bin/python

import logging
from flotype.bridge import Bridge 

bridge = Bridge(log_level=logging.DEBUG, api_key='abcdefgh')

class ChatServer(bridge.Service):
    def join(self, name, handler, callback):
        print('Got join request for %s.' % (name))
        bridge.join_channel('lobby', handler, callback)

def start_server():
    def on_client_join(lobby):
        print("Client joined lobby (%s)." % (lobby))
    chat = ChatServer()
    bridge.publish_service('chatty', chat, on_client_join)

bridge.ready(start_server)
