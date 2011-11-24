import uuid
import weakref

class NowObject(object):
    def __init__(self, parent=None, **kwargs):
        self.children = weakref.WeakValueDictionary()

        self.is_original = False

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
                self.is_original = True

            self.root = self.parent.root
            if name:
                self.parent.register(self)
    
    def register(self, other):
        print 'REGISTER SELF', self, 'HAS CHILD', other
        self.children[ other.pathchain[0] ] = other

    def __getattr__(self, key):
        if key.startswith('handle_'):
            return None
        pathchain = list(self.pathchain)
        pathchain.append(key)
        return NowObject(parent=self, pathchain=pathchain)

    def fullpath(self):
        x = []
        y = self
        while y:
            print 'ADDING', y.pathchain
            x.insert(0, '[' + '.'.join(y.pathchain) + ']' )
            y = y.parent
        
        fp = '.'.join(x)
        return fp

    def __repr__(self):
        return '<' + self.__class__.__name__ + ' PathHistory: ' + self.fullpath() + '>'
    
    def __call__(self, *args, **kwargs):
        wrapped_args = args
        wrapped_kwargs = kwargs
        return self.root.call(self.pathchain, *wrapped_args, **wrapped_kwargs)

    def call(self, pathchain, *args, **kwargs):
        pathchain = list(pathchain)

        if not pathchain:
            print 'END OF PATHCHAIN', self
            return self

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

        return ChatRoom(self.root)

def main():    
    # Root Object the client interfaces with
    now = NowObject()
    default = NowObject(now, name='default')
    auth = AuthService(default, name='auth')

    room = now.default.auth.login(username='enki', password='secret')
    print now.default.children.items()
    print 'room', room
    print 'SENDMESSAGE', room.send_message()
    
    print getattr(now, room.pathchain[0])()

if __name__ == '__main__':
    main()