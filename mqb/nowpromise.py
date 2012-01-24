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