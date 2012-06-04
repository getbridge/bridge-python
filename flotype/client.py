from flotype import serializer

class Client(object):
    def __init__(self, bridge, id):
        self.bridge, self.clientId = bridge, id;
    def get_service(self, svc):
        return reference.Reference(self, ['client', id, svc])
