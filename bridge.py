import logging

class Bridge(object):
    def __init__(self, **kwargs):
        self.url = kwargs.get('url', 'http://localhost:8080/bridge')
        self.reconnect = kwargs.get('reconnect', True)
        self.tcp = kwargs.get('tcp', False)

        self.host = kwargs.get('host', 'localhost')
        self.port = kwargs.get('port', 8090)

        self.log = logging.getLogger(__name__)
        self.log.setLevel(kwargs.get('logLevel', logging.ERROR))

        self._system =
        self._system =



  var system = {
    hook_channel_handler: function(name, handler, callback){
      self.children['channel:' + name] = self.children[handler._getRef()._pathchain[2]];
      if (callback) {
        callback.call( self.getChannel(name), name );
      }
    },
    getservice: function(name, callback){
      callback.call(self.children[name]);
    }
  };

    def ready(self, handler):
        pass

    def publishService(self, name, server, callback):
        pass

    def joinChannel(self, name, handler, callback):
        pass

    def establishConnection(self):
        pass

class Connection(object):
    DEFAULT_EXCHANGE = 'T_DEFAULT'

    def __init__(self, bridge):
        self.bridge = bridge
        self.bridge.establishConnection()

    def reconnect(self):


  util.info("Attempting reconnect");
  if (!this.connected && this.interval < 12800) {
    this.establishConnection();
    setTimeout(this.reconnect, this.interval *= 2);
  }
