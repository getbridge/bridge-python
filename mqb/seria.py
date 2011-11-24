import uuid
import weakref

class NowPromise(object):
    def __init__(self):
        self.cb = None
        self.result = None
        self.have_result = False
    
    def __call__(self):
        return self

    def callback(self, cb):
        self.cb = cb
        self.check_fire()
    
    def set_result(self, result):
        if isinstance(result, NowPromise):
            result.callback(self.set_result)
        else:
            self.result = result
            self.have_result = True
            self.check_fire()
    
    def check_fire(self):
        if self.cb and self.have_result:
            self.cb(self.result)

    def __getattr__(self, funcname):
        def callme(*args, **kwargs):
            self.callback( lambda x: getattr(x, funcname)(*args, **kwargs) )
        return callme

class NowObject(object):
    def __init__(self, parent=None, **kwargs):
        self.children = weakref.WeakValueDictionary()

        self.is_original = False

        self.parent = parent

        if not self.parent:
            self.root = self
            self.pathchain = []
            self.is_original = True
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
            x.insert(0, '[' + '.'.join(y.pathchain) + ']' )
            y = y.parent
        
        fp = '.'.join(x)
        return fp

    def __repr__(self):
        return '<' + self.__class__.__name__ + ' PathHistory: ' + self.fullpath() + '>'
    
    def __call__(self, *args, **kwargs):
        return self.mycall(self.pathchain, *args, **kwargs)
    
    def mycall(self, pathchain, *args, **kwargs):
        if not self.is_original:
            print 'NOT ORIGINAL', self, pathchain
            return self.parent.mycall(pathchain, *args, **kwargs)
        else:   
            print 'ORIGINAL', self, pathchain
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
            promise = NowPromise()
            promise.set_result( handler(*args, **kwargs) )
            return promise
        
        print self
        raise AttributeError(next)
    
class ChatRoom(NowObject):
    def send_message(self, message):
        print 'Hello', message 

class AuthService(NowObject):
    def handle_login(self, username, password):
        print 'LOGIN'

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

    print '---'

    room = now.default.auth.login(username='enki', password='secret')
    room.callback(prnt)

    print 'room', room
    room.send_message('WORLD')

    print '---'
    print auth.roominfo()
    
    # print getattr(now, room.pathchain[0])()

if __name__ == '__main__':
    main()