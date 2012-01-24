import functools

class AttrDict(dict):
    def __init__(self, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)
    def __getattr__(self, name):
        return self[name]

def waitForAll(callback, tasks):
    completed = {}
    finished = False
    def retfun(key, *args):
        assert not finished, 'Finishing twice not permitted.'
        completed[key] = args
        # print 'retfun', len(completed), len(tasks), key, retfun, args
        if len(completed) == len(tasks):
            callback(completed)

    if not tasks:
        callback(completed)

    if isinstance(tasks, dict):
        for key, task in tasks.iteritems():
        # print 'calling key', key, task
            task[0](callback=functools.partial(retfun, key), *task[1], **task[2])
    else:
        for key, task in enumerate(tasks):
            task[0](callback=functools.partial(retfun, key), *task[1], **task[2])