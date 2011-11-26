import uuid
import weakref
import functools

class PromiseTreeResolver(object):
    def __init__(self, tree, callback):
        self.tree = tree
        self.callback = callback
        self.waiting = set()
        self.fired = False

        self.do_resolve([], self.tree)
        if not self.waiting and not self.fired:
            self.callback(self.tree)

    def fulfillPromise(self, data, path=None):
        if path:
            self.updateTree(path, data)
        else:
            self.tree = data
        
        self.waiting.remove(path)

        if not self.waiting:
            self.fired = True
            self.callback(self.tree)

    def updateTree(self, origpath, data):
        path = list(origpath)

        pivot = self.tree
        while len(path) > 1:
            pivot = pivot[path.pop(0)]
        
        pivot[path.pop(0)] = data

    def registerPromise(self, pivot, path):
        tpath = tuple(path)
        self.waiting.add( tpath )
        pivot.callback( functools.partial(self.fulfillPromise, path=tpath) )

    def do_resolve(self, path, pivot):
        if isinstance(pivot, dict):
            for key, value in pivot.items():
                self.do_resolve(path + [key], value)
        elif isinstance(pivot, list):
            for (pos, elem) in enumerate(pivot):
                self.do_resolve(path + [pos], elem)
        elif isinstance(pivot, basestring):
            pass
        elif isinstance(pivot, int):
            pass
        elif isinstance(pivot, float):
            pass
        elif isinstance(pivot, NowPromise):
            self.registerPromise(pivot, path)
        else:
            print 'unknown element', pivot

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
            promise = NowPromise()
            self.callback( lambda x: promise.set_result(getattr(x, funcname)(*args, **kwargs)) )
            return promise
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

    def callback(self, cb):
        return cb(self)

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

class ChatServer(NowObject):
    def join_room(self, room_name):
        print 'JOIN', room_name
        return ChatRoom(self, name=room_name)

    def handle_roominfo(self, room):
        print 'ROOMINFO', room

class AuthService(NowObject):
    def setup(self):
        self._chatserver = ChatServer(self, name='chat')

    def handle_login(self, username, password):
        print 'LOGIN', username, password
        if password == 'secret':
            return self._chatserver
        else:
            return None
    
def prnt(*args):
    print 'PRNT', ' '.join( repr(x) for x in args )

def test_basic():    
    # Root Object the client interfaces with
    now = NowObject()
    auth = AuthService(now, name='auth')
    public_chat = ChatServer(now, name='chat')

    now.chat().callback(prnt)

    private_chat = now.auth.login(username='enki', password='secret')
    private_chat.callback(prnt)

    flotype = private_chat.join_room('flotype')
    print 'GOT', flotype
    flotype.callback(prnt)
    flotype.send_message('WORLD')

    print '---'
    private_chat.roominfo(flotype)

def test_resolver():
    promise = NowPromise()
    tree =  {'just': {'yet': ['another', promise,] } }
    ptree = PromiseTreeResolver(tree, prnt)
    promise.set_result('foo')

def main():
    #test_basic()
    test_resolver()

if __name__ == '__main__':
    main()