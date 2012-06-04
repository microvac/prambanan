import prambanan
from .native import *

__author__ = 'h'

class ElementStack(object):

    def __init__(self, el):
        self.current = el
        self.stack = []

    u = el_stack_push
    o = el_stack_pop
    t = el_stack_text
    a = el_stack_attr

class PageTemplate(object):

    def __init__(self, __render):
        self.__render  = __render

    def render(self, el, encoding=None, translate=None, target_languange=None, **vars):
        stack = ElementStack(el)
        econtext = dict(vars)
        econtext["repeat"] = lambda name, it: [0, len(it)]
        rcontext = dict()
        self.__render(stack, econtext, rcontext)

        return stack.current

