import unittest
from chameleon.zpt.template import PageTemplate
import os
from prambanan.zpt.compiler.ptparser import PTParser
from zpt.template import ZPTTemplate

dir = os.path.dirname(os.path.realpath(__file__))

zpt_dir = os.path.join(dir, "zpt")
gen_dir = os.path.join(zpt_dir, "gen")
if not os.path.exists(gen_dir):
    os.makedirs(gen_dir)

template = ZPTTemplate()
print template.get_imports(("prambanan", "test/template/template.pt"))

class TestZpt(unittest.TestCase):

    def test_translate(self):
        name = "bindrepeat"
        parser = PTParser(os.path.join(zpt_dir, name+".pt"), binds=True)
        print parser.code
