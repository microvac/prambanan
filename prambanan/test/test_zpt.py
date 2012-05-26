import unittest
import os
from StringIO import StringIO
from prambanan.zpt.compiler.ptparser import PTParser

dir = os.path.dirname(os.path.realpath(__file__))

zpt_dir = os.path.join(dir, "template")
gen_dir = os.path.join(zpt_dir, "gen")

class TestZpt(unittest.TestCase):

    def test_translate(self):
        name = "template"
        parser = PTParser(os.path.join(zpt_dir, name+".pt"))
        with open(os.path.join(gen_dir, name+".py"), "w") as f:
            f.write(parser.code)