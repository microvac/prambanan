import prambanan
from .native import *

__author__ = 'h'

def escape(c):
    return c

class ElementStack(object):

    def __init__(self, el):
        self.current = el
        self.stack = []
        self.replay_el = None
        self.tail = None

    u = el_stack_push
    o = el_stack_pop
    t = el_stack_text
    a = el_stack_attr

    def capture(self):
        self.u("span")
        replay_el = self.current
        self.o()
        result = ElementStack(replay_el)
        result.replay_el = replay_el
        return result

    def capture_for_repeat(self):
        result = ElementStack(self.current)
        return result

    replay = el_stack_replay

    def repeat(self, tag):
        self.u(tag)
        self.repeat_el = self.current

class RepeatItem(object):

    def __init__(self, iterator, length):
        self._iterator = iterator
        self.length = length
        self.index = None

    def _next(self):
        if self.index is None:
            self.index = 0
        else:
            self.index += 1
        index = self.index
        self.start = index == 0
        self.end = index == self.length -1
        self.number = index + 1
        self.odd = index  % 2 == 1
        self.even = index  % 2 == 0

def RepeatDict(d):

    def c(key, iterable):
        length = len(iterable)
        iterator = iter(iterable)
        if prambanan.is_js:
            c[key] = RepeatItem(iterator, length)
            return c[key]
        else:
            d[key] = RepeatItem(iterator, length)
            return d[key]

    if not prambanan.is_js:
        c.__setitem__ = d.__setitem__
        c.__getitem__ = d.__getitem__

    return c

class PageTemplate(object):

    def __init__(self, __render):
        self.__render  = __render

    def render(self, el, model, encoding=None, translate=None, target_languange=None, **vars):
        stack = ElementStack(el)
        econtext = dict(vars)
        econtext["repeat"] = RepeatDict({})
        rcontext = dict()
        self.__render(stack, model, econtext, rcontext)

        return stack.current

