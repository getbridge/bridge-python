#!/usr/bin/python

import logging
from bridge import Bridge 

bridge = Bridge(log_level=logging.DEBUG, api_key='abcdefgh', reconnect=False)

class ChatServer(object):
    def join(self, name, handler, callback):
        print('Got join request for %s.' % (name))
        bridge.join_channel('lobby', handler, callback)

def start_server():
    print("start_server called (from chatserver.py)")

    def on_client_join(lobby):
        print("Client joined lobby (%s)." % (lobby))

    bridge.publish_service('chatserver', ChatServer, on_client_join)

bridge.ready(start_server)
