class Event(object):
    _callbacks = {}

    def on(self, name, callback):
        if not name in self._callbacks:
            self._callbacks[name] = []
        self._callbacks[name].append(callback)
        return self

    def off(self, name, callback):
        if not name in self._callbacks:
            self._callbacks[name] = []
        callbacks = self._callbacks[name]
        for i in xrange(len(callbacks) - 1, -1, -1):
            if callbacks[i] == callback:
                del callbacks[i]
        return self

    def trigger(self, name, *args):
        if name in self._callbacks:
            for callbacks in self._callbacks[name]:
                callbacks(*args)
        return self

class Model(Event):
    """
    """
    idAttribute = "id"

    def __init__(self, attributes=None, options=None):
        if attributes is None:
            attributes = {}

        self.cid = ""
        self.id = None
        self.attributes = {}
        self.set(attributes, {"silent":True})

    def validate(self, attributes=None):
        pass

    def isValid(self):
        return self.validate(self.toJSON()) is None

    def isNew(self):
        return self.id is None

    def get(self, name):
        if name in self.attributes:
            return self.attributes[name]
        return None

    def set(self, attrs, options=None):
        if options is None:
            options = {}

        changes = {}
        for key in iter(attrs):
            value = attrs[key]
            if value != self.get(key):
                changes[key] = value
                self.attributes[key] = value
                if "silent" not in options or not options["silent"]:
                    self.trigger("change:"+key, self, value)

        if len(changes) > 0:
            if "silent" not in options or not options["silent"]:
                self.trigger("change", self, changes)

    def clear(self, options=None):
        if options is None:
            options = {}
        self.attributes.clear()
        if "silent" not in options or not options["silent"]:
            self.trigger("change")

    def clone(self):
        return self.__class__(self.attributes)

    def toJSON(self):
        return self.attributes.copy()

    def fetch(self, options=None):
        raise NotImplementedError()

    def save(self, value=None, options=None):
        raise NotImplementedError()

    def destroy(self, options=None):
        raise NotImplementedError()

    def changedAttributes(self, diff=None):
        raise NotImplementedError()

    def hasChanged(self, attr=None):
        raise NotImplementedError()

    def __eq__(self, other):
        try:
            other_attrs = other.attributes
        except AttributeError:
            return False

        return other_attrs == self.attributes



class Collection(object):
    pass
