import logging
from collections import namedtuple, defaultdict

from twisted.internet import reactor

class Bridge(object):
    def __init__(self, **kwargs):
        self.log = logging.getLogger(__name__)
        self.log.setLevel(kwargs.get('logLevel', logging.ERROR))
        self.reconnect = kwargs.get('reconnect', True)

        self._events = defaultdict(list)
        self._connected = False
        self._connection = Connection(self)
        self._children = {
            'system': _SystemService(self)
        }

        # Client-only.
        self.url = kwargs.get('url', 'http://localhost:8080/bridge')

        # Server-only.
        self.host = kwargs.get('host', 'localhost')
        self.port = kwargs.get('port', 8090)

    def on(self, name, func):
        self._events[name].append(func)
        return self

    def emit(self, name, *args):
        if name in self._events:
            for func in self._events[name]:
                func(*args)
        return self

    def removeEvent(self, name, func):
        if name in self._events:
            self._events[name].remove(func)
        return self

    def onReady(self):
        self.log.info('Handshake complete.')
        if not self.connected:
            self.connected = True
            self.emit('ready')

    def onMessage(self, msg):
        deserialize(msg)



    def ready(self, handler):
        pass

    def publish_service(self, name, server, callback):
        pass

    def join_channel(self, name, handler, callback):
        pass


PathChain = namedtuple('PathChain', 'type, route, service, method')

class _SystemService(object):
    def __init__(self, bridge):
        self.bridge = bridge

    def hook_channel_handler(self, name, handler, callback=None):
        service_name = handler.pathchain.service
        service = self.bridge._children[service_name]
        self.bridge._children['channel:' + name] = service
        if callback:
            callback(self.bridge.getChannel(name), name)

    def get_service(self, name, callback):
        if name in self.bridge._children:
            callback(self.bridge._children[name])
        else:
            callback(None, 'Cannot find service {0}.'.format(name))

    def remote_error(self, msg):
        self.bridge.log.warn(msg)
        self.bridge._emit('remoteError', msg)

class Connection(object):
    DEFAULT_EXCHANGE = 'T_DEFAULT'

    def __init__(self, bridge):
        self.bridge = bridge
        self.establish_connection()

    def reconnect(self):
        self.bridge.log.info('Attempting reconnect.')
        if not self.connected and self.interval < 12800:
            self.establish_connection()
            self.interval *= 2
            reactor.callLater(self.interval, self.reconnect)

    def establish_connection(self):
        self.bridge.log.info('Starting TCP connection (%s:%s).',
                             self.bridge.host, self.bridge.port)
        self.sock =




Connection.prototype.establishConnection = function () {
  var self = this,
      Bridge = this.Bridge;

  // Select between TCP and SockJS transports
  if (this.options.tcp) {
    util.info('Starting TCP connection', this.options.host, this.options.port);
    this.sock = new TCP(this.options).sock;
  } else {
    util.info('Starting SockJS connection');
    this.sock = new SockJS(this.options.url, this.options.protocols, this.options.sockjs);
  }

  this.sock.onmessage = function (message) {
    util.info("clientId and secret received", message.data);
    var ids = message.data.toString().split('|');
    self.clientId = ids[0];
    self.secret = ids[1];
    self.interval = 400;

    self.sock.onmessage = function(message){
      try {
        message = util.parse(message.data);
        util.info('Received', message);
        Bridge.onMessage(message);
      } catch (e) {
        util.error("Message parsing failed: ", e.message, e.stack);
      }
    };
    Bridge.onReady();
  };

  this.sock.onopen = function () {
    util.info("Beginning handshake");
    var msg = {command: 'CONNECT', data: {session: [self.clientId || 0, self.secret || 0]}};
    msg = util.stringify(msg);
    self.sock.send(msg);
  };

  this.sock.onclose = function () {
    util.warn("Connection closed");
    self.connected = false;
    if (self.options.reconnect) {
      // do reconnect stuff. start at 100 ms.
      self.reconnect();
    }
  };
};

