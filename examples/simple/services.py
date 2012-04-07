from flotype.bridge import Bridge 
bridge = Bridge(api_key='abcdefgh')


#
# Publishing a Bridge service
#
# Any Javascript object can be published. A published service 
# can be retrieved by any Bridge client with the same API key pair.
#
# Only Bridge clients using the prviate API key may publish services.
#
class TestService(object):
    def ping(self, cb):
        print 'Received ping request!'
        cb('Pong')
        
bridge.publish_service('testService', TestService())


#
# Retrieving a Bridge service 
#
# This can be done from any Bridge client connected to the same 
# Bridge server, regardless of language.
# If multiple clients publish a Bridge service, getService will 
# retrieve from the publisher with the least load.
#
def message_cb(msg):
    print msg
    
testService = bridge.get_service('testService')
print 'Sending ping request'
testService.ping(message_cb)

bridge.connect()

