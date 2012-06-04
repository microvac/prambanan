from logilab.astng.exceptions import UnresolvableName, InferenceError

def infer(node):
    try:
       for inferred in node.infer():
           yield inferred
    except (UnresolvableName, InferenceError):
        pass

def infer_qname(node):
    infer_result = list(infer(node))
    if len(infer_result) == 1:
        return infer_result[0].qname()
    else:
        return None
