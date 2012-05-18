import prambanan.native as native
from prambanan.jslib import underscore

is_server = native.is_server

items = underscore.items

def JS(fn):
    return fn

def JSNoOp(target):
    return target

def select(fn, server, client):
    return server if is_server else client


