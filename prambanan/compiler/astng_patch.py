from logilab.astng import nodes
from logilab.astng.bases import YES, path_wrapper
from logilab.astng.exceptions import InferenceError
import logilab.astng.protocols as protocols

def infer_subscript(self, context=None):
    """infer simple subscription such as [1,2,3][0] or (1,2,3)[-1]"""
    if isinstance(self.slice, nodes.Index):
        index = self.slice.value.infer(context).next()
        if index is YES:
            yield YES
            return
        try:
            if hasattr(self.value, "getitem"):
                assigned = self.value.getitem(index.value, context)
                for infered in assigned.infer(context):
                    yield infered
                return
            else:
                has_infer_item = False
                for l in self.value.infer():
                    if l is not YES and hasattr(l, "infer_item"):
                        has_infer_item = True
                        for inferred in l.infer_item(index, context):
                            yield inferred
                if not has_infer_item:
                    raise InferenceError()
        except AttributeError:
            raise InferenceError()
        except (IndexError, TypeError):
            yield YES
            return
    else:
        raise InferenceError()

nodes.Subscript.infer = path_wrapper(infer_subscript)

def infer_ifexp(self, context=None):
    for inferred in self.body.infer(context):
        yield inferred
    for inferred in self.orelse.infer(context):
        yield inferred
nodes.IfExp.infer = path_wrapper(infer_ifexp)

prev_infer_argname = protocols._arguments_infer_argname
def arguments_infer_argname(self, name, context):
    if hasattr(self, "arg_types") and name in self.arg_types:
        yield self.arg_types[name]
    else:
        for inferred in prev_infer_argname(self, name, context):
            yield inferred
protocols._arguments_infer_argname = arguments_infer_argname



