from flotype.bridge import Bridge
    
bridge = Bridge(api_key='abcdefgh', host='localhost', port=8090) # new code: using public key

class ChatHandler(object):
    def message(self, sender, message):
        print (sender + ':' + message)

def join_callback(channel, name):
    channel.message('steve', 'Can write to channel ' + name)

auth = bridge.get_service('auth')
auth.join('flotype-lovers', 'secret123', ChatHandler(), join_callback)

bridge.connect()
