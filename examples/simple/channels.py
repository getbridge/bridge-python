from BridgePython.bridge import Bridge 
bridge = Bridge(api_key='myapikey')


#
# Joining a Bridge channel
#
# In order to join a Bridge channel, clients must provide the name 
# of the channel to join and a handler object on which RPC calls 
# in the channel will act on. Note that the client that is joined 
# to the channel is whoever created the handler, not necessarily the 
# client executing the join command. This means clients can join other
# clients to channels by having a reference to an object of theirs.
#
# Only Bridge clients using the private API key may call the join command. 
# However, those clients may join other clients using the public API key on their behalf.
#
def start():
    class TestHandler(object):
        def log(self, msg):
            print('Got message: %s' % (msg));

    bridge.join_channel('testChannel', TestHandler(), callback=ready)


#
# Getting and calling a Bridge channel
#
# This can be done from any Bridge client connected to the same 
# Bridge server, regardless of language.
# When a function call is made to a channel object, the requested
# function will be executed on everyone in the channel
# 
# Only Bridge clients using the private API key may call the join command. 
#
def ready(*args):
    testChannel = bridge.get_channel('testChannel')
    print 'Sending message'
    testChannel.log('hello')

bridge.connect(start)

