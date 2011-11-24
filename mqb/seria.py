import uuid

class NowObject(object):
    def __init__(self, parent=None, **kwargs):
        self.children = {}

        self.parent = parent

        if not self.parent:
            self.root = self
            self.pathchain = []
        else:
            self.pathchain = kwargs.get('pathchain', [])
            name = None
            if not self.pathchain:
                name = kwargs.get('name', uuid.uuid4().hex)
                self.pathchain = [name]

            self.root = self.parent.root
            if name:
                self.parent.register(self)
    
    def register(self, other):
        self.children[ other.pathchain[0] ] = other

    def __getattr__(self, key):
        if key.startswith('handle_'):
            return None
        pathchain = list(self.pathchain)
        pathchain.append(key)
        return NowObject(parent=self, pathchain=pathchain)

    def __repr__(self):
        return '<' + self.__class__.__name__ + ' ' + '.'.join(self.pathchain) + '>'
    
    def __call__(self, *args, **kwargs):
        wrapped_args = args
        wrapped_kwargs = kwargs
        return self.root.call(self.pathchain, *wrapped_args, **wrapped_kwargs)

    def call(self, pathchain, *args, **kwargs):
        pathchain = list(pathchain)

        next = pathchain.pop(0)

        child = self.children.get(next, None)
        if child:
            return child.call(pathchain, *args, **kwargs)

        handler = getattr(self, 'handle_' + next)
        if handler:
            return handler(*args, **kwargs)
        
        raise AttributeError(next)

class ChatRoom(NowObject):
    def send_message(self):
        return 'lala'

class AuthService(NowObject):
    def handle_login(self, username, password):
        print 'LOGIN'

        return ChatRoom(parent=self)

def main():    
    # Root Object the client interfaces with
    now = NowObject()

    default = NowObject(now, name='default')
    auth = AuthService(default, name='auth')

    room = now.default.auth.login(username='enki', password='secret') 

    print 'room', room
    print 'SENDMESSAGE', room.send_message()

if __name__ == '__main__':
    main()