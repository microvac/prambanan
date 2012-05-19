def always_one(fn):
    def res(*args):
        return 1
    return res

def add_x(x):
    def res(fn):
        def wrapped(a, b):
            return fn(x, b)
        return wrapped
    return res

def add(x, y):
    return x+y

@always_one
def add2(x, y):
    return x+y

@add_x(10)
def add3(x, y):
    return x+y

print add(3, 4)
print add2(3, 4)
print add3(5, 4)

