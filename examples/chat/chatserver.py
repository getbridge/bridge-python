from BridgePython.bridge import Bridge

class AuthHandler(object):
  def join(self, room, password, obj, callback):
    if password == "secret123":
      print ('Welcome!')
      # new: join channel using the client's objects
      bridge.join_channel(room, obj, callback) 
    else:
      print ('Sorry!')

bridge = Bridge(api_key='myapikey')
bridge.publish_service('auth', AuthHandler())

bridge.connect()