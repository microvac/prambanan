from logilab.astng import nodes
from logilab.astng.bases import YES, path_wrapper
from logilab.astng.exceptions import InferenceError

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

