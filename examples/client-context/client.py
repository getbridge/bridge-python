from BridgePython import Bridge
bridge = Bridge(api_key='myapikey')

class PongHandler(object):
    def pong(self):
        print ("PONG!")

bridge.store_service("pong", PongHandler())
bridge.get_service("ping").ping()

bridge.connect()

