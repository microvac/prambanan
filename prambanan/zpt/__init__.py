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

    def __next(self):
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

    def __call__(key, iterable):
        length = len(iterable)
        iterator = iter(iterable)
        __call__[key] = RepeatItem(iterator, length)
        return __call__[key]

    return __call__

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

