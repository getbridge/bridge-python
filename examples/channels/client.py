from BridgePython.bridge import Bridge
bridge = Bridge(api_key='myapikey')

class ChatHandler(object):
    def message(self, sender, message):
        print (sender + ':' + message)

def join_callback(channel, name):
    print "Joined channel: %s" % name
    # The following RPC call will fail because client was not joined to channel with write permissions
    channel.message('steve', 'This should not work')

auth = bridge.get_service('auth')
auth.join('bridge-lovers', ChatHandler(), join_callback)

bridge.connect()
