from prambanan.jslib import underscore
from prambanan.native import *

def JS(fn):
    return fn

def JSNoOp(target):
    return target

def select(fn, server, client):
    return server if is_server else client


