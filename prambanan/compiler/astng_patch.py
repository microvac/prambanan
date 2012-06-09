from logilab.astng.exceptions import InferenceError, NotFoundError
import logilab.astng
import logilab.astng.bases as bases
import logilab.astng.protocols as protocols
import logilab.astng.builder
import logilab.astng.scoped_nodes

class Instance(bases.Instance):

    def igetattr(self, name, context=None):
        """inferred getattr"""
        if hasattr(self._proxied, "attr_types") and name in self._proxied.attr_types:
            yield self._proxied.attr_types[name]
            return

        found = False

        try:
            # XXX frame should be self._proxied, or not ?
            get_attr = self.getattr(name, context, lookupclass=False)
            for inferred in bases._infer_stmts(self._wrap_attr(get_attr, context), context,frame=self):
                yield inferred
            found = True
        except (NotFoundError, InferenceError):
            pass

        try:
            # fallback to class'igetattr since it has some logic to handle
            # descriptors
            for inferred in  self._wrap_attr(self._proxied.igetattr(name, context),context):
                yield inferred
            found = True
        except (NotFoundError, InferenceError):
            pass

        if not found:
            raise InferenceError(name)

bases.Instance = protocols.Instance = logilab.astng.Instance = logilab.astng.builder.Instance = logilab.astng.scoped_nodes.Instance = Instance


prev_infer_argname = protocols._arguments_infer_argname
def arguments_infer_argname(self, name, context):
    if hasattr(self, "arg_types") and name in self.arg_types:
        yield self.arg_types[name]
    else:
        for inferred in prev_infer_argname(self, name, context):
            yield inferred
protocols._arguments_infer_argname = arguments_infer_argname


from logilab.astng import nodes
from logilab.astng.bases import YES, path_wrapper

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

def for_assigned_stmts(self, node, context=None, asspath=None):
    if asspath is None:
        for lst in self.iter.infer(context):
            if isinstance(lst, (nodes.Tuple, nodes.List)):
                if hasattr(lst, "infer_item"):
                    for item in lst.infer_item(None, context):
                        yield item
                else:
                    for item in lst.elts:
                        yield item
    else:
        for infered in protocols._resolve_looppart(self.iter.infer(context),
            asspath, context):
            yield infered

nodes.For.assigned_stmts = bases.raise_if_nothing_infered(for_assigned_stmts)

