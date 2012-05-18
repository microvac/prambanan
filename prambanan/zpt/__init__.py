__author__ = 'h'

def getitem(econtext, name, default):
    pass

def deleteitem(econtext, name, backup, default):
    pass

def convert_str(str):
    pass

def lookup_attr(obj, key):
    try:
        return getattr(obj, key)
    except AttributeError as exc:
        try:
            get = obj.__getitem__
        except AttributeError:
            raise exc
        try:
            return get(key)
        except KeyError:
            raise exc

