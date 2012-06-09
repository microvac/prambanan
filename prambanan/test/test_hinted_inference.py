import unittest
import prambanan.compiler.astng_patch

from logilab.astng import InferenceError, builder, nodes
from prambanan.cmd import patch_astng_manager
from prambanan.compiler.manager import PrambananManager
from prambanan.compiler.scopegenerator import ScopeGenerator

manager = PrambananManager([])
builder = builder.ASTNGBuilder(manager)
patch_astng_manager(manager)

def get_name_node(start_from, name, index=0):
    return [n for n in start_from.nodes_of_class(nodes.Name) if n.name == name][index]

def get_node_of_class(start_from, klass):
    return start_from.nodes_of_class(klass).next()

class TestHintedTypeInference(unittest.TestCase):

    def test_float_complex_ambiguity(self):
        code = '''
def test_anu(lst):
    """
    prambanan:type lst l(t(i(int), i(str)))
    """
    for a,b in lst:
        print a
        '''
        astng = builder.string_build(code, __name__, __file__)
        sgen = ScopeGenerator("test", astng)
        sgen.visit(astng)
        a = astng["test_anu"]["a"]
        for inferred in a.infer():
            print inferred
        b = astng["test_anu"]["b"]
        for inferred in b.infer():
            print inferred


