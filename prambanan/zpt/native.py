from lxml import etree

__all__ = ["getitem", "deleteitem", "convert_str", "lookup_attr", "el_stack_attr", "el_stack_pop", "el_stack_push", "el_stack_text"]

def getitem(econtext, name, default):
    return econtext.get(name, default)

def deleteitem(econtext, name, backup, default):
    pass

def convert_str(s):
    return str(s)

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


def el_stack_push(self, tag):
    child = etree.SubElement(self.current, tag)
    self.stack.append(self.current)
    self.current = child

def el_stack_pop(self):
    self.current = self.stack.pop()

def el_stack_text(self, text):
    if self.current.text is None:
        self.current.text = text
    else:
        self.current.text = self.current.text + text

def el_stack_attr(self, name, value):
    self.current.attrib[name] = value


