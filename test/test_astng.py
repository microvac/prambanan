import os
import unittest
from logilab.astng import BUILTINS_MODULE, builder, nodes, InferenceError, NotFoundError
from logilab.astng.nodes import Module
from logilab.astng.bases import YES, BUILTINS_NAME
from logilab.astng.as_string import as_string
from logilab.astng.manager import ASTNGManager

MANAGER = ASTNGManager()


_dir = os.path.dirname(os.path.realpath(__file__))
bare_dir = os.path.join(_dir, "output")

class TestAstNg(unittest.TestCase):

    def test_translate(self):
        name = "class"
        astng = builder.ASTNGBuilder().file_build(os.path.join(bare_dir, name+'.py'))
        print astng
        for item in astng["Class1"]["method1"].lookup("self"):
            print item


