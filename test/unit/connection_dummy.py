class ConnectionDummy():
    def __init__(self):
        self.messages = []
        self.onopened = False

    def onopen(self, *args):
        self.onopened = True

    def onclose(self, *args):
        return

    def onmessage(data, tcp):
        messages += data['data']

