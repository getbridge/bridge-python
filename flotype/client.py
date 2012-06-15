from flotype import serializer, reference

class Client(object):
    def __init__(self, bridge, id):
        self.bridge, self.clientId = bridge, id;
    def get_service(self, svc):
        return reference.Reference(self.bridge, ['client', self.clientId, svc])
