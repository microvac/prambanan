from logilab.astng.bases import Instance
from logilab.astng.exceptions import UnresolvableName, InferenceError
from logilab.astng.node_classes import Const

def infer(node):
    try:
       for inferred in node.infer():
           yield inferred
    except (UnresolvableName, InferenceError):
        pass

def infer_one(node):
    infer_result = list(infer(node))
    if len(infer_result) == 1:
        return infer_result[0]
    else:
        return None

def infer_qname(node):
    infer_result = infer_one(node)
    if infer_result is not None:
        return infer_result.qname()
    else:
        return None

def inferred_is_of_class(inferred, *args):
    if inferred.__class__ in [Instance, Const]:
        cls = inferred._proxied
        for arg in args:
            if arg == cls:
                return True
        return False
    else:
        return False

def inferred_is_instance(inferred, *args):
    if inferred.__class__ in [Instance, Const]:
        cls = inferred._proxied
        for arg in args:
            if arg == cls:
                return True
            for ancestor in cls.ancestors():
                if arg == ancestor:
                    return True
        return False
    else:
        return False

def is_instance(node, *args):
    found = False
    for inferred in infer(node):
        if inferred_is_instance(inferred, *args):
            found = True
        else:
            return False
    return found

class ConstEvaluator(object):
    def visit(self, node):
        return getattr(self, "visit_"+node.__class__.__name__.lower())(node)

    def visit_name(self, n):
        res = infer_one(n)
        if res is None:
            raise ValueError("cannot infer %n" % n.name)
        return self.visit(res)

    def visit_const(self, const):
        return const.value

    def visit_tuple(self, t):
        result = []
        for elt in t.elts:
            result.append(self.visit(elt))
        return tuple(result)

    def visit_list(self, l):
        result = []
        for elt in l.elts:
            result.append(self.visit(elt))
        return result
