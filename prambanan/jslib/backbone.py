class Model(object):
    def __init__(self, attrs = {}):
        self.attrs = attrs
    def get(self, name):
        if(not name in self.attrs):
            return None
        return self.attrs[name]
    def set(self, attrs):
        for key in attrs:
            self.attrs[key] = attrs[key]

class Collection(object):
    def __init__(self, attrs = {}):
        self.attrs = attrs

