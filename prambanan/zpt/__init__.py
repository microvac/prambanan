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

class TemplateRegistry(object):
    def __init__(self):
        self.registry = {}

    def get_namespace(self, namespace):
        if namespace not in self.registry:
            self.registry[namespace] = {}
        return self.registry[namespace]

    def register(self, namespace, name, render):
        nm = self.get_namespace(namespace)
        template = PageTemplate(render)
        nm[name] = template
        return template

    def get(self, config):
        namespace, name = config
        if not prambanan.is_js and (namespace not in self.registry or name not in self.registry[namespace]):
            registry_register_py(self, namespace, name)

        if namespace not in self.registry:
            raise KeyError("namespace %s not in template registry" % namespace)
        nm = self.registry[namespace]
        if name not in nm:
            raise KeyError("template %s not in template namespace %s" % (name, namespace))

        return nm[name]