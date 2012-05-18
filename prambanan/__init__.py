import prambanan.native as native

is_server = native.is_server

def JS(fn):
    return fn

def JSNoOp(target):
    return target

def select(fn, server, client):
    return server if is_server else client
