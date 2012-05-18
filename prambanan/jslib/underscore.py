class Chain(object):
    def __init__(self, val):
        self.val = val
    def __getattribute__(self, name):
        if not name in ["val", "value"]:
            def method(*args):
                self.val = _.__getattribute__(name)(self.val, *args)
                return self
            return method
        return object.__getattribute__(self, name)
    def value(self):
        return self.val


def chain(obj):
    return Chain(obj)

def find(list, it):
    for o in list:
        if it(o):
            return o
    return None

def each(obj, it, context = None):
    keys = []
    try:
        keys = obj.keys()
    except Exception:
        for o in obj:
            it(o)
        return

    for key in keys:
        it(obj[key])

def map(list, it, context=None):
    return map(it, list)

def filter(list, it, context=None):
    return filter(it, list)

def reduce(list, it, memo, context=None):
    return reduce(it, list, memo)

def isUndefined(obj):
    return obj is None

def items(obj):
    return obj.items()

detect = find
