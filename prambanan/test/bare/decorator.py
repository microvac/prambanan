def cache(fn):
    return fn

def cache2(fn, anu):
    return fn

@cache
def cached_method(i):
    return i * 4;

@cache()
def cached_method2(i):
    return i * 4;

@cache2(3)
def cached_method3(i):
    return i * 4;

@cache2(3)
@cache
@cache2(3)
@cache
def cached_method4(i):
    return i * 4;

def cached_method5(i):
    return i * 4;

@cache2(anu=3)
class Anu(obj):
    i = 4
