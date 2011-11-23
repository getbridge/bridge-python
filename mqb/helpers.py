class AttrDict(dict):
    def __init__(self, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)
    def __getattr__(self, name):
        return self[name]

def waitForAll(callback, tasks):
    completed = {}
    finished = False
    def retfun(key, data):
        assert not finished, 'Finishing twice not permitted.'
        completed[key] = data
        print 'retfun', len(completed), len(tasks), key, retfun, data
        if len(completed) == len(tasks):
            callback(completed)

    for key, task in tasks.iteritems():
        print 'calling key', key, task
        task[0](callback=functools.partial(retfun, key), *task[1], **task[2])
