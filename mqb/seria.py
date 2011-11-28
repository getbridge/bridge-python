import uuid
import weakref
import functools
import types

from nowpromise import NowPromise

from nowpromise import NowPromise
from promisetree import PromiseTreeResolver

class NowObject(object):
    def __init__(self, parent=None, name=None, resolving=False, exchange=None, **kwargs):
        self.children = weakref.WeakValueDictionary()

        self.is_original = False

        self.exchange = None

        self.parent = parent

        if not self.parent:
            self.root = self
            # self.name = ''
            self.name = name or uuid.uuid4().hex
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
        
        if exchange:
            self.exchange = exchange

        self.setup()
    
    def setup(self):
        pass # abstract

    def callback(self, cb):
        return cb(self)

    def register(self, other):
        # print 'REGISTER CHILD', self, other.name
        self.children[ other.name ] = other

    def __getattr__(self, key):
        if key.startswith('handle_'):
            return None
        return NowObject(parent=self, name=key, resolving=True)

    def full_path(self):
        x = []
        y = self
        while y:
            x.insert(0, y.name )
            y = y.parent
        
        # fp = '.'.join(x)
        return x

    def __repr__(self):
        return '<' + self.__class__.__name__ + ' Path: ' + '.'.join(self.full_path()) + '>'
    
    def __call__(self, *args, **kwargs):
        promise = NowPromise()

        unresolved_args = [args, kwargs]
        arg_resolver = PromiseTreeResolver(unresolved_args)
        arg_promise = arg_resolver.resolve()
        arg_promise.callback( functools.partial(self.receive_resolved_args, promise) )
        
        return promise

    def receive_resolved_args(self, promise, resolved_args):
        args = resolved_args[0]
        kwargs = resolved_args[1]

        retval = self.prepcall([], *args, **kwargs)
        retval_resolver = PromiseTreeResolver(retval)
        retval_promise = retval_resolver.resolve()
        
        retval_promise.callback( promise.set_result )
    
    def prepcall(self, pathchain, *args, **kwargs):
        if not self.is_original:
            pathchain.insert(0, self.name)
            return self.parent.prepcall(pathchain, *args, **kwargs)
        else:   
            return self.call(pathchain, *args, **kwargs)

    def handle_end(self, *args, **kwargs):
        print 'END OF PATHCHAIN', self, args, kwargs
        return self

    def call(self, pathchain, *args, **kwargs):
        pathchain = list(pathchain)

        if not pathchain:
            return self.handle_end(*args, **kwargs)

        next = pathchain.pop(0)

        child = self.children.get(next, None)
        if child:
            return child.call(pathchain, *args, **kwargs)

        handler = getattr(self, 'handle_' + next)
        if handler:
            if not pathchain:
                return handler(*args, **kwargs)
            else:
                raise AttributeError("handler with remaining path %s" % (pathchain))
        
        return self.not_found([next] + pathchain, args, kwargs)
    
    def not_found(self, pathchain, args, kwargs):
        raise AttributeError( pathchain[0] )
    
class NowClient(NowObject):
    def serialize_args_kwargs(self, args, kwargs):
        serialized_args = self.traverse(args)
        serialized_kwargs = self.traverse(kwargs)
        return serialized_args, serialized_kwargs

    def traverse(self, pivot):
        # print 'WHUT', pivot, type(pivot)
        if type(pivot) in (tuple, list):
            result = ('list', [self.traverse(elem) for elem in pivot])
        elif isinstance(pivot, dict):
            result = ('dict', dict([(key, self.traverse(value)) for key, value in pivot.items()]))
        elif type(pivot) in (str, unicode, basestring):
            result = ('str', pivot)
        elif type(pivot) in (int, float):
            result = ('float', pivot)
        # elif isinstance(pivot, types.FunctionType):
        #     wrap = NowObject(self)
        #     wrap.handle_end = pivot
        #     result = ('now', wrap.full_path())
        elif isinstance(pivot, NowObject):
            result = ('now', pivot.full_path())
        elif isinstance(pivot, type(None)):
            result = ('none', None)
        else:
            raise Exception("Unknown %s" % (type(pivot)))
        
        return result

    def retraverse(self, tup):
        typ, pivot = tup
        if typ == 'list':
            result = [self.retraverse(x) for x in pivot]
        elif typ == 'dict':
            result = dict( (x, self.retraverse(y)) for x,y in pivot.items() )
        elif typ == 'str':
            result = unicode(pivot)
        elif typ == 'float':
            result = float(pivot)
        elif typ == 'now':
            bar = self.root
            while pivot:
                foo = pivot.pop(0)
                bar = getattr(bar,foo)
            result = bar
        elif typ == 'none':
            result = None
        else:
            raise Exception("Unknown %s" % (typ, ))

        return result

    def rebuild_args_kwargs(self, serargskwargs):
        args = self.retraverse(serargskwargs[0])
        kwargs = self.retraverse(serargskwargs[1])
        return args, kwargs

    def remote_call(self, pathchain, args, kwargs):
        # print 'REMOTE CALL', pathchain, args, kwargs
        serargskwargs = self.serialize_args_kwargs(args, kwargs)

        self.exchange.send(pathchain, serargskwargs)

    def not_found(self, pathchain, args, kwargs):
        # print 'NOT FOUND', self, pathchain, self.children.keys()
        return self.remote_call(pathchain, args, kwargs)

    def message_received(self, pathchain, serargskwargs):
        print 'MESSAGE RECEIVED', self, pathchain, serargskwargs

        args, kwargs = self.rebuild_args_kwargs(serargskwargs)
        print 'REBUILT', args, kwargs

        bar = self
        while pathchain:
            # print 'DEEP', bar
            foo = pathchain.pop(0)
            bar = getattr(bar, foo)
        
        bar(*args, **kwargs)

