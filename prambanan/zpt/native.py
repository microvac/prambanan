from lxml import etree
import pkg_resources

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

class LazyPageTemplate(object):

    def __init__(self, package, filename):
        self.package = package
        self.filename = filename

    def render(self, el, **vars):
        from prambanan.zpt import PageTemplate
        from prambanan.zpt.compiler.ptparser import PTParser

        file = pkg_resources.resource_filename(self.package, self.filename)
        pt = PTParser(file)
        compiled = compile(pt.code, self.filename, "exec")
        env = {}
        exec(compiled, env)
        return PageTemplate(env["render"]).render(el, **vars)

def registry_register_py(self, package, filename):
    template = LazyPageTemplate(package, filename)
    nm = self.get_namespace(package)
    nm[filename] = template
    return template
