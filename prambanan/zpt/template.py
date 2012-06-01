from lxml import etree


class ElementStack(object):

    def __init__(self, el):
        self.current = el
        self.stack = []

    def push(self, tag):
        child = etree.SubElement(self.current, tag)
        self.stack.append(self.current)
        self.current = child
    u = push

    def pop(self):
        self.current = self.stack.pop()
    o = pop

    def text(self, text):
        if self.current.text is None:
            self.current.text = text
        else:
            self.current.text = self.current.text + text
    t = text

    def attr(self, name, value):
        self.current.attrib[name] = value
    a = attr

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

class LazyPageTemplate(object):

    def __init__(self, package, filename):
        self.package = package
        self.filename = filename

    def render(self, el, **vars):
        import pkg_resources
        from prambanan.zpt.compiler.ptparser import PTParser

        file = pkg_resources.resource_filename(self.package, self.filename)
        pt = PTParser(file)
        compiled = compile(pt.code, self.filename, "exec")
        env = {}
        exec(compiled, env)
        return PageTemplate(env["render"]).render(el, **vars)


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

    def register_py(self, package, filename):
        import os

        template = LazyPageTemplate(package, filename)
        name,ext = os.path.splitext(filename)
        nm = self.get_namespace(package)
        nm[name] = template
        return template

    def get(self, namespace, name):
        if namespace not in self.registry:
            raise KeyError("namespace %s not in template registry" % namespace)
        nm = self.registry[namespace]
        if name not in nm:
            raise KeyError("template %s not in template namespace %s" % (name, namespace))
        return nm[name]
