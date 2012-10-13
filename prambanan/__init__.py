from .native import *

def JS(fn):
    return fn

def JS_noop_marker(target):
    return target

@JS_noop_marker
def JS_noop(target):
    return target

def select(fn, py, js):
    return js if is_js else py

def to_qname(cls):
    return "%s:%s" % (cls.__module__, cls.__name__)

def load_qname(qname):
    module_name, attr = qname.split(":")
    module = __import__(module_name)
    splitted = module_name.split(".")
    for i in range(1, len(splitted)):
        module = getattr(module, splitted[i])
    return getattr(module, attr)
