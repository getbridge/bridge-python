from BridgePython import Bridge
bridge = Bridge(api_key='myapikey')

class PingHandler(object):
    def ping(self):
        print ("PING!")
        calling_client = bridge.context()
        ponger = calling_client.get_service("pong")
        ponger.pong("PONG!")

bridge.publish_service("ping", PingHandler())
bridge.connect()
