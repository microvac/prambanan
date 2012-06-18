from lxml import etree

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

def remove_el(el):
    pass

def el_stack_push(self, tag):
    child = etree.SubElement(self.current, tag)
    self.stack.append(self.current)
    self.current = child
    self.tail = None

def el_stack_pop(self):
    self.tail = self.current
    self.current = self.stack.pop()

def el_stack_text(self, text):
    if self.tail is not None:
        if self.tail.tail is None:
            self.tail.tail = text
        else:
            self.tail.tail = self.tail.tail + text
    else:
        if self.current.text is None:
            self.current.text = text
        else:
            self.current.text = self.current.text + text

def el_stack_attr(self, name, value):
    self.current.attrib[name] = value

def el_stack_replay(self, tag):
    pass



