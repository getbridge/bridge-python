#!/usr/bin/python

import logging
from bridge import Bridge, Service

bridge = Bridge(log_level=logging.DEBUG)

class ChatServer(Service):
    def join(self, name, handler, callback):
        print('Got join request for %s.' % (name))
        bridge.join_channel('lobby', handler, callback)

def start_server():
    print("start_server called (from chatserver.py)")

    def on_client_join(lobby):
        print("Client joined lobby (%s)." % (lobby))

    bridge.publish_service('chatserver', ChatServer(), on_client_join)

bridge.ready(start_server)
