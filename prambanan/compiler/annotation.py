from logilab.astng import nodes

available_processors = {}

def processor(name):
    def decorate(c):
        available_processors[name] = c
        return c
    return decorate

def parse(node, context):
    doc = node.doc
    results = {}
    processors = {}

    for name, p in available_processors.items():
        processors[name] = p(context)
        results[name] = []

    for line in doc.splitlines():
        stripped = line.strip()
        if stripped.startswith("prambanan:"):
            splitted = stripped.split(" ",1)
            name = splitted[0][len("prambanan:"):]
            if name in processors:
                processor = processors[name]
                if processor is not None:
                    arg = splitted[1] if len(splitted) > 1 else None
                    result = processors[name].process(node, arg)
                    results[name].append(result)
            else:
                context.warn("cannot find annotation processor %s" % name)

    return results

def make_class(make, next):
    return make(next)._proxied

def make_list_infer_item(child):
    def infer_item(i, context):
        yield child
    return infer_item

def make_list(make, next):
    result = nodes.List()
    if len(next) > 0:
        result.infer_item = make_list_infer_item(make(next))
    return result

def make_instance(node, qname):
    modname, classname = qname.rsplit(".", 1)
    return node.root().import_module(modname)[classname].instanciate_class()

type_makers = {
    "list": make_list,
    "class": make_class
}

@processor("type")
class TypeAnnotation(object):

    def __init__(self, context):
        self.context = context

    def process(self, node, str):
        splitted = str.split(" ", 1)
        varname = splitted[0]

        type_text = splitted[1]
        type_confs = type_text.split(" ")

        def make(confs):
            current = confs[0]
            if current in type_makers:
                return type_makers[current](make, confs[1:])
            return make_instance(node, current)

        return varname, make(type_confs)
