import uuid
import weakref

class NowPromise(object):
    def __init__(self):
        self.cbs = []
        self.result = None
        self.have_result = False
    
    def __call__(self):
        return self

    def callback(self, cb):
        self.cbs.append(cb)
        self.check_fire()
    
    def set_result(self, result):
        assert not self.have_result, 'Can only fire once'
        if isinstance(result, NowPromise):
            result.callback(self.set_result)
        else:
            self.result = result
            self.have_result = True
            self.check_fire()
    
    def check_fire(self):
        if self.cbs and self.have_result:
            while self.cbs:
                cb = self.cbs.pop()
                cb(self.result)

    def __getattr__(self, funcname):
        def callme(*args, **kwargs):
            self.callback( lambda x: getattr(x, funcname)(*args, **kwargs) )
        return callme

class NowObject(object):
    def __init__(self, parent=None, name=None, resolving=False, **kwargs):
        self.children = weakref.WeakValueDictionary()

        self.is_original = False

        self.parent = parent

        if not self.parent:
            self.root = self
            self.name = ''
            self.is_original = True
        else:
            self.name = name
            if not self.name:
                self.name = uuid.uuid4().hex
                self.is_original = True

            self.root = self.parent.root

            if not resolving:
                self.is_original = True

            if self.is_original:
                self.parent.register(self)
        
        self.setup()
    
    def setup(self):
        pass # abstract

    def register(self, other):
        self.children[ other.name ] = other

    def __getattr__(self, key):
        if key.startswith('handle_'):
            return None
        return NowObject(parent=self, name=key, resolving=True)

    def fullpath(self):
        x = []
        y = self
        while y:
            x.insert(0, y.name )
            y = y.parent
        
        fp = '.'.join(x)
        return fp

    def __repr__(self):
        return '<' + self.__class__.__name__ + ' Path: ' + self.fullpath() + '>'
    
    def __call__(self, *args, **kwargs):
        return self.prepcall([], *args, **kwargs)
    
    def prepcall(self, pathchain, *args, **kwargs):
        if not self.is_original:
            pathchain.insert(0, self.name)
            return self.parent.prepcall(pathchain, *args, **kwargs)
        else:   
            return self.call(pathchain, *args, **kwargs)

    def call(self, pathchain, *args, **kwargs):
        pathchain = list(pathchain)

        if not pathchain:
            print 'END OF PATHCHAIN', self
            promise = NowPromise()
            promise.set_result(self)
            return promise

        next = pathchain.pop(0)

        child = self.children.get(next, None)
        if child:
            promise = NowPromise()
            promise.set_result( child.call(pathchain, *args, **kwargs) )
            return promise

        handler = getattr(self, 'handle_' + next)
        if handler:
            if not pathchain:
                promise = NowPromise()
                promise.set_result( handler(*args, **kwargs) )
                return promise
            else:
                raise AttributeError("handler with remaining path %s" % (pathchain))
        
        print self
        raise AttributeError(next)
    
class ChatRoom(NowObject):
    def send_message(self, message):
        print 'Hello', message 

class AuthService(NowObject):
    def handle_login(self, username, password):
        print 'LOGIN', username, password

        return ChatRoom(self.root)
    
    def handle_roominfo(self, room):
        print 'ROOMINFO', room

def prnt(*args):
    print 'PRNT', ' '.join( repr(x) for x in args )

def main():    
    # Root Object the client interfaces with
    now = NowObject()
    default = NowObject(now, name='default')
    auth = AuthService(default, name='auth')

    room = now.default.auth.login(username='enki', password='secret')
    room.callback(prnt)

    room.send_message('WORLD')

    print '---'
    auth.roominfo(room)

if __name__ == '__main__':
    main()