from BridgePython import Bridge
bridge = Bridge(api_key='myapikey')

class ChatHandler(object):
    def message(self, sender, message):
        print (sender + ':' + message)

def join_callback(channel, name):
    print "Joined channel: %s" % name
    # The following RPC call will succeed because client was joined to channel with write permissions
    channel.message('steve', 'Can write to channel')

auth = bridge.get_service('auth')
auth.join_writeable('bridge-lovers', "secret123", ChatHandler(), join_callback)

bridge.connect()

