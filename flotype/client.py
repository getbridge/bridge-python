from flotype import serializer

class Client(object):
    def __init__(self, bridge, id):
        self.bridge, self.clientId = bridge, id;
    def getService(self, svc, cb):
        self.bridge._connection.sendCommand(
            'GETOPS', {name: svc,
                       client: this.clientId,
                       callback: serializer.serialize(this._bridge,cb)})
