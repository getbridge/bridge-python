from BridgePython.bridge import Bridge
    
bridge = Bridge(api_key='myapikey') # new code: using public key

class ChatHandler(object):
    def message(self, sender, message):
        print (sender + ':' + message)
    
def join_callback(channel, name):
    print ("Joined channel : " + name)
    channel.message('steve', 'Bridge is pretty nifty')

auth = bridge.get_service('auth')
auth.join('bridge-lovers', 'secret123', ChatHandler(), join_callback)

bridge.connect()