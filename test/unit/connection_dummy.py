class ConnectionDummy():
    def __init__(self):
        self.messages = []
        self.onopened = False
        self.options = {'host': 'localhost', 'port': 8090}

    def onopen(self, *args):
        self.onopened = True

    def onclose(self, *args):
        return

    def onmessage(data, tcp):
        messages += data['data']

