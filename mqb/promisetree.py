from nowpromise import NowPromise
import types

class PromiseTreeResolver(object):
    def __init__(self, tree):
        self.tree = tree

        if isinstance(self.tree, tuple):
            self.tree = list(self.tree)

        self.waiting = set()
        self.fired = False

    def resolve(self):
        self.masterpromise = NowPromise()
        self.do_resolve([], self.tree)
        if not self.waiting and not self.fired:
            self.masterpromise.set_result(self.tree)
        return self.masterpromise

    def fulfillPromise(self, data, path=None):
        if path:
            self.updateTree(path, data)
        else:
            self.tree = data
        
        self.waiting.remove(path)

        if not self.waiting and not self.fired:
            self.fired = True
            self.masterpromise.set_result(self.tree)

    def updateTree(self, origpath, data):
        path = list(origpath)

        pivot = self.tree
        while len(path) > 1:
            nextkey = path.pop(0)
            if isinstance(pivot[nextkey], tuple):
                pivot[nextkey] = list(pivot[nextkey])
            pivot = pivot[nextkey]
        
        pivot[path.pop(0)] = data

    def registerPromise(self, pivot, path):
        tpath = tuple(path)
        self.waiting.add( tpath )
        pivot.callback( functools.partial(self.fulfillPromise, path=tpath) )

    def do_resolve(self, path, pivot):
        from seria import NowObject
        if isinstance(pivot, dict):
            for key, value in pivot.items():
                self.do_resolve(path + [key], value)
        elif isinstance(pivot, list) or isinstance(pivot,tuple):
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
        elif isinstance(pivot, NowObject):
            pass
        elif isinstance(pivot, type(None)):
            pass
        elif isinstance(pivot, tuple):
            pass
        elif isinstance(pivot, types.FunctionType):
            pass
        else:
            print 'unknown element', pivot