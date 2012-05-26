from prambanan.jslib import underscore
from prambanan.native import *

def JS(fn):
    return fn

def JSNoOp(target):
    return target

def select(fn, py, js):
    return js if is_js else py
