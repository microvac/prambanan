from prambanan.jslib import underscore
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
