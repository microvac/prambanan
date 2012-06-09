from logilab.astng import nodes
from pyparsing import Word, alphanums, Forward, commaSeparatedList, Group, Suppress, Optional, OneOrMore
import logging

logger = logging.getLogger("prambanan")
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
        processors[name] = p()
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
                logger.warn("cannot find hint processor '%s' in scope '%s'" % (name,  node.scope().qname()))

    return results

ELEMENT = Forward()
EREF = Group(ELEMENT)

ID = Word(alphanums+".")
TYPE = Group((ID+Suppress(":")+ID | ID))

INSTANCE = ("i("+TYPE+")")
CLASS = "c("+TYPE+")"
LIST = "l("+EREF+")"
DICT ="d("+EREF+","+EREF+")"
TUPLE = "t("+OneOrMore(EREF+Suppress(Optional(",")))+")"
ELEMENT << (INSTANCE | CLASS | LIST | DICT | TUPLE)
ELEMENT << (INSTANCE | CLASS | LIST | DICT | TUPLE)

def make_tuple_infer_item(children):
    def infer_item(i, context):
        yield children[i]
    return infer_item

def make_tuple(make, get_class, args):
    nexts = [make(a) for a in args]
    result = nodes.Tuple()
    result.elts = nexts
    return result

def make_list_infer_item(child):
    def infer_item(i, context):
        yield child
    return infer_item


def make_list(make, get_class, args):
    result = nodes.List()
    if len(args[0]) > 0:
        next = make(args[0])
        result.itered = lambda: [next]
        result.infer_item = make_list_infer_item(next)
    return result

def make_instance(make, get_class, args):
    conf = args[0]
    if len(conf) == 2:
        modname, classname = conf
    else:
        modname = "__builtin__"
        classname = conf[0]
    return get_class(modname, classname).instanciate_class()

def make_class(make, get_class, args):
    conf = args[0]
    if len(conf) == 2:
        modname, classname = conf
    else:
        modname = "__builtin__"
        classname = conf[0]
    return get_class(modname, classname)

type_makers = {
    "l(": make_list,
    "t(": make_tuple,
    "c(": make_class,
    "i(": make_instance,
}

@processor("type")
class TypeHintProcessor(object):

    def process(self, node, str):
        splitted = str.split(" ", 1)
        varname = splitted[0]

        type_text = splitted[1]
        type_confs = ELEMENT.parseString(type_text)

        get_class = lambda a, b:  node.root().import_module(a)[b]

        def make(confs):
            current = confs[0]
            if current in type_makers:
                return type_makers[current](make, get_class, confs[1:-1])
            return make_instance(node, current)

        return varname, make(type_confs)
