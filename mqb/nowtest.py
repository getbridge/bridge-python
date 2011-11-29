from seria import NowObject, NowClient

class Exchange(object):
    def __init__(self):
        self.clients = {}
    
    def register(self, client):
        # print 'REGISTER', client.name
        self.clients[client.name] = client
    
    def send(self, pathchain, serargskwargs):
        self.clients[ pathchain[0] ].message_received(pathchain[1:], serargskwargs)

class ChatRoom(NowObject):
    def send_message(self, message):
        print 'Hello', message 

class ChatServer(NowObject):
    def join_room(self, room_name):
        print 'JOIN', room_name
        return ChatRoom(self, name=room_name)

    def handle_roominfo(self, room):
        print 'ROOMINFO', room
        room.callback(prnt)
        return {'hello': 5}

class AuthService(NowObject):
    def setup(self):
        self._chatserver = ChatServer(self, name='chat')

    def handle_login(self, username, password, callback=None):
        print 'LOGIN', username, password
        if password == 'secret':
            result = self._chatserver
        else:
            result = None
        
        print '--- READY FOR CALLBACK ---'
        if callback:
            callback('alalala')
        return None
    
def prnt(*args):
    print 'PRNT', ' '.join( repr(x) for x in args )

def test_remote():
    exchange = Exchange()

    server = NowClient(name='default', exchange=exchange)
    exchange.register(server)
    auth = AuthService(server, name='auth')

    now = NowClient(exchange=exchange)
    exchange.register(now)
    
    class Foo(NowObject):
        def handle_got_result(self, result):
            print 'GOT RESULT', result

    bar = Foo(now, name='foo')

    now.default.auth.login(username='enki', password='secret', callback=bar.got_result )


def test_new():    
    # Root Object the client interfaces with
    now = NowObject()
    auth = AuthService(now, name='auth')
    public_chat = ChatServer(now, name='chat')

    now.auth().callback(prnt)


def test_basic():    
    # Root Object the client interfaces with
    now = NowObject()
    auth = AuthService(now, name='auth')
    public_chat = ChatServer(now, name='chat')

    # now.chat().callback(prnt)

    private_chat = now.auth.login(username='enki', password='secret')
    private_chat.callback(prnt)

    flotype = private_chat.join_room('flotype')
    print 'GOT', flotype
    flotype.callback(prnt)
    flotype.send_message('WORLD')

    print '---'
    roominfo = private_chat.roominfo(flotype)
    roominfo.callback(prnt)







def test_resolver():
    promise = NowPromise()
    tree =  {'just': {'yet': ['another', promise,] } }
    ptree = PromiseTreeResolver(tree)
    masterpromise = ptree.resolve()
    masterpromise.callback(prnt)
    promise.set_result('foo')


def main():
    # test_new()
    # test_basic()
    # test_resolver()
    test_remote()

if __name__ == '__main__':
    main()