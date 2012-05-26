from lxml import etree


class ElementStack(object):

    def __init__(self, el):
        self.current = el
        self.stack = []

    def push(self, tag):
        child = etree.Element(tag)
        self.current.append(tag)
        self.stack.append(self.current)
        self.current = child
        return self
    u = push

    def pop(self):
        self.current = self.stack.pop()
        return self
    o = pop

    def text(self, text):
        self.current.append(text)
        return self
    t = text

    def attr(self, name, value):
        self.attributes[name] = value
        return self
    a = attr



