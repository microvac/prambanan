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
    n = el_stack_node

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

    def render(self, el, model, vars=None):
        if vars is None:
            vars = {}

        stack = ElementStack(el)
        econtext = dict(vars)
        econtext["repeat"] = RepeatDict({})
        rcontext = dict()
        self.__render(stack, model, econtext, rcontext)

        return stack.current

def bind_change_attr(parent, bind_ons, bind_last_on_change):
    result = None
    if len(bind_ons):
        attr = bind_ons[0]
        current = None
        next_on_change = None
        event_name = "change:%s"%attr
        def on_change_attr():
            global current, next_on_change
            if current:
                current.off(event_name, next_on_change)
            next_on_change = None
            if parent:
                current = parent.get(attr)
            if current:
                next_on_change = bind_change_attr(current, bind_ons[1:], bind_last_on_change)
                current.on("change", next_on_change)
                next_on_change()
        result = on_change_attr
    else:
        result = bind_last_on_change(parent)
    result()
    return result

def bind_change(model, bind_ons, bind_attrs, on_change):
    def bind_last_on_change(last_model):
        if len(bind_attrs):
            for attr in bind_attrs:
                last_model.on("change:%s"%attr, on_change)
        else:
            last_model.on("change",on_change)
        return on_change

    bind_change_attr(model, bind_ons, bind_last_on_change)

def bind_repeat(collection, col_on_add):
    el_map = {}
    def on_add(model):
        el_map[model.cid] = col_on_add(model)
    def on_remove(model):
        remove_el(model.cid)
        del el_map[model.cid]
    def on_reset(models):
        global el_map
        for cid in el_map:
            remove_el(el_map[cid])
        el_map = {}
        if models:
            for model in models:
                on_add(model)

    for model in collection:
        on_add(model)

    collection.on("add", on_add)
    collection.on("remove", on_remove)
    collection.on("reset", on_reset)

def bind_replay(bindable, events, on_event):
    for event in events:
        bindable.on(event, on_event)
    on_event()
