import uuid
import weakref
import functools
import types

from nowpromise import NowPromise

from nowpromise import NowPromise
from promisetree import PromiseTreeResolver

from mqblib import MQBConnection, waitForAll, AttrDict


class NowObject(object):
    def __init__(self, parent=None, name=None, resolving=False, **kwargs):
        self.children = dict() #weakref.WeakValueDictionary()

        self.is_original = False

        self.is_namespaced = True

        self.parent = parent

        if not self.parent:
            self.root = self
            self.name = ''
            self.public_name = uuid.uuid4().hex
            self.is_original = True
        else:
            self.is_namespaced = parent.is_namespaced
            self.name = self.public_name = name
            if not self.name:
                self.name = self.public_name = uuid.uuid4().hex
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
        # print 'REGISTER CHILD', self, other.name
        self.children[ other.name ] = other

    def __setitem__(self, key, obj):
        # print 'SETITEM', key, obj
        true_self = self.find_original()
        obj(parent=true_self, name=key)

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

    def public_path(self):
        x = []
        y = self
        while y:
            x.insert(0, y.public_name )
            y = y.parent
        
        # fp = '.'.join(x)
        return x

    def __repr__(self):
        return '<' + self.__class__.__name__ + ' Path: ' + '.'.join(self.full_path()) + ' '  + repr(self.is_namespaced)  + '>'
    
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

        retval = self.prepcall([], self.is_namespaced, *args, **kwargs)
        retval_resolver = PromiseTreeResolver(retval)
        retval_promise = retval_resolver.resolve()
        
        retval_promise.callback( promise.set_result )
    
    def find_original(self, pathchain=[]):
        pathchain = list(pathchain)
        if not self.is_original:
            pathchain.append(self.name)
            return self.parent.find_original(pathchain)
        else:
            return self.find_child(pathchain)
    
    def find_child(self, pathchain):
        if pathchain:
            return self.children[pathchain.pop(0)].find_child(pathchain)
        else:
            return self

    def prepcall(self, pathchain, is_namespaced, *args, **kwargs):
        if not self.is_original:
            pathchain.insert(0, self.name)
            return self.parent.prepcall(pathchain, is_namespaced, *args, **kwargs)
        else:   
            return self.call(pathchain, is_namespaced, *args, **kwargs)

    def handle_end(self, *args, **kwargs):
        print 'END OF PATHCHAIN', self, args, kwargs
        return self

    def call(self, pathchain, is_namespaced, *args, **kwargs):
        pathchain = list(pathchain)

        if not pathchain:
            return self.handle_end(*args, **kwargs)

        next = pathchain.pop(0)

        child = self.children.get(next, None)
        if child:
            return child.call(pathchain, is_namespaced, *args, **kwargs)

        handler = getattr(self, 'handle_' + next)
        if handler:
            if not pathchain:
                return handler(*args, **kwargs)
            else:
                raise AttributeError("handler with remaining path %s" % (pathchain))
        
        return self.not_found([next] + pathchain, is_namespaced, args, kwargs)
    
    def not_found(self, pathchain, is_namespaced, args, kwargs):
        raise AttributeError( pathchain[0] )
    
    def serialize_args_kwargs(self, args, kwargs):
        add_links = set()
        serialized_args= self.traverse(args, add_links)[1]
        serialized_kwargs = self.traverse(kwargs, add_links)[1]
        serargskwargs = (serialized_args, serialized_kwargs)
        return serargskwargs, add_links

    def traverse(self, pivot, add_links_set):
        # print 'WHUT', pivot, type(pivot)
        if type(pivot) in (tuple, list):
            result = ('list', [self.traverse(elem, add_links_set) for elem in pivot])
        elif isinstance(pivot, dict):
            result = ('dict', dict([(key, self.traverse(value, add_links_set)) for key, value in pivot.items()]))
        elif type(pivot) in (str, unicode, basestring):
            result = ('str', pivot)
        elif type(pivot) in (int, float):
            result = ('float', pivot)
        elif isinstance(pivot, types.FunctionType):
            wrap = NowObject(self._local)
            wrap.handle_end = pivot
            result = ('now', {'ref': [x for x in wrap.full_path() if x]})
        elif isinstance(pivot, NowObject):
            result = ('now', {'ref': [x for x in pivot.full_path() if x]})
        elif isinstance(pivot, type(None)):
            result = ('none', None)
        else:
            raise Exception("Unknown %s" % (type(pivot)))
        
        if result[0] == 'now':
            need_add = result[1]['ref'][0]
            # print 'ADD LINK FOR', need_add
            add_links_set.add(need_add)

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
            pivot = pivot['ref']
            while pivot:
                foo = pivot.pop(0)
                bar = getattr(bar,foo)
            bar.is_namespaced = False
            # print 'BAR', bar.is_namespaced
            result = bar
        elif typ == 'none':
            result = None
        else:
            raise Exception("Unknown %s" % (typ, ))

        return result

    def rebuild_args_kwargs(self, serargskwargs):
        args = self.retraverse( ["list", serargskwargs[0] ] )
        kwargs = self.retraverse( ["dict", serargskwargs[1] ] )
        return args, kwargs

    def message_received(self, pathchain, serargskwargs):
        print 'MESSAGE RECEIVED', self, pathchain, serargskwargs

        args, kwargs = self.rebuild_args_kwargs(serargskwargs)

        bar = self
        if pathchain[0] != self.public_name:
            pathchain = [self.public_name] + pathchain
        while pathchain:
            # print 'DEEP', bar
            foo = pathchain.pop(0)
            bar = getattr(bar, foo)
        
        bar.is_namespaced = False
        # print 'REBUILT', bar, args, kwargs
        bar(*args, **kwargs)


class CallProxy:
    def __init__(self, target):
        self.queue = []
        self.target = target
        self.fired = False
    
    def reflect(self):
        self.fired = True
        for x in self.queue:
            getattr(self.target, x[0])(*x[1], **x[2])

    def __getattr__(self, key):
        tar = getattr(self.target, key)
        if not isinstance(tar, types.MethodType):
            return tar
        if self.fired:
            return tar
        def foo(*args, **kwargs):
            self.queue.append( [key, args, kwargs] )
        return foo

class NowClient(NowObject):
    def __init__(self, *args, **kwargs):
        NowObject.__init__(self)

        self._local = NowObject(parent=self, name=self.public_name)
        self.children['local'] = self._local

        self.mqbconn = MQBConnection(client_id=self.public_name, *args, **kwargs)
        self.mqbconn.connect(self.connection_made)
        self.mqbconn.message_received = self.message_received

        self.mqb = CallProxy(self.mqbconn)
    
    def _subscribe_channel(self, name):
        pass

    def _unsubscribe_channel(self, name):
        pass

    def _join_workerpool(self, name, callback=lambda x: x):
        pool_queue_name = 'W_' + name
        def got_queue(promise, result):
            # print 'GOT QUEUE', promise, result
            self.mqb.listen(queue=pool_queue_name)
            self.mqb.bind_queue(queue=pool_queue_name, exchange=self.mqb.DEFAULT_EXCHANGE, routing_key='N.' + name, callback=lambda x,y: callback(name) )
        
        self.mqb.declare_queue(queue=pool_queue_name, callback=got_queue)

    def _leave_workerpool(self, name):
        pass

    @property
    def system(self):
        return AttrDict({
            'subscribe_channel': self._subscribe_channel,
            'unsubscribe_channel': self._unsubscribe_channel,
            'join_workerpool': self._join_workerpool,
            'leave_workerpool': self._leave_workerpool,
            # 'connect_namespace': self._connect_namespace,
            # 'disconnect_namespace': self._disconnect_namespace,
        })

    def connection_made(self):
        print 'CONNECTION MADE'
        self.mqb.reflect()
    
    def not_found(self, pathchain, is_namespaced, args, kwargs):
        print 'NOT FOUND', self, pathchain, is_namespaced, 'CALLING REMOTE'
        serargskwargs, add_links = self.serialize_args_kwargs(args, kwargs)

        # print 'ADD LINKS HEADERS REQUESTED', add_links

        def did_send(promise, result):
            print 'SENT', promise, result
        # did_send = None

        self.mqb.send( pathchain[0], is_namespaced, pathchain, serargskwargs, add_links=add_links, callback=did_send)
