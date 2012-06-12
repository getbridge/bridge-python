from flotype.bridge import Bridge

class AuthHandler(object):
  def join(self, obj, callback):
    print ('Welcome!')
    bridge.join_channel('+rw', obj, True, callback)
    bridge.join_channel('+r', obj, False, callback)

bridge = Bridge(api_key='abcdefgh', host='localhost', port=8090)
bridge.publish_service('auth', AuthHandler())

bridge.connect()
