#!/usr/bin/python

import bridge
import logging

bridge = bridge.Bridge(log_level=logging.DEBUG)

class ChatServer(bridge.Service):
    def join(self, name, handler, callback):
        print('%s is joining the lobby.' % (name))
        bridge.join_channel('lobby', handler, callback)

def start_server():
    def on_client_join():
        print("Client joined the lobby.")

    bridge.publish_service('chatserver', ChatServer, on_client_join)

bridge.ready(start_server)
