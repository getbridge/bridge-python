from flotype.bridge import Bridge
bridge = Bridge(api_key='myapikey')

class AuthHandler(object):

  def join(self, channel_name, obj, callback):
    # Passing false means the client cannot write to the channel
    bridge.join_channel(channel_name, obj, False, callback)

  def join_writeable(self, channel_name, secret_word, obj, callback):
    # Passing true means the client can write to the channel as well as read from it
    if secret_word == "secret123":
        bridge.join_channel(channel_name, obj, True, callback)

bridge.publish_service('auth', AuthHandler())

bridge.connect()
