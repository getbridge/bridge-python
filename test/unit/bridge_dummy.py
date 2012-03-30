import reference_dummy

class BridgeDummy():
    def __init__(self):
        self.options = { 'redirector': 'http://redirector.flotype.com',
                         'reconnect': True,
                         'log': 2 # 0 for no output
                        }
        self.stored = []
    
    def _store_object(self, handler, ops):
        self.stored.append([handler, ops])
        return reference_dummy.ReferenceDummy()

    def _send(self, args, destination):
        self.last_args = args
        self.last_dest = destination
