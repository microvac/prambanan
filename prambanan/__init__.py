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

def load_module_attr(module_attr):
    module_name, attr = module_attr.split(":")
    module = __import__(module_name)
    splitted = module_name.split(".")
    for i in range(1, len(splitted)):
        module = getattr(module, splitted[i])
    return getattr(module, attr)
