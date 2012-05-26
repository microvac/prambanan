import unittest
from chameleon.zpt.template import PageTemplate
import os
from lxml import etree
import pkg_resources
from StringIO import StringIO
from prambanan.zpt.compiler.ptparser import PTParser
from prambanan.zpt.template import TemplateRegistry

dir = os.path.dirname(os.path.realpath(__file__))

zpt_dir = os.path.join(dir, "template")
gen_dir = os.path.join(zpt_dir, "gen")

class TestZpt(unittest.TestCase):

    def test_translate(self):
        name = "template"
        parser = PTParser(os.path.join(zpt_dir, name+".pt"))
        with open(os.path.join(gen_dir, name+".py"), "w") as f:
            f.write(parser.code)

class TestZptRegistry(unittest.TestCase):

    def test_render(self):
        print "prambanan"
        print ""
        print ""
        registry = TemplateRegistry()
        registry.register_py("prambanan", "test/template/template.pt")
        pt = registry.get("prambanan", "test/template/template")
        el = etree.Element("div")
        el = pt.render(el, a="lalal", b=["c", "d"], c=True, width=500, anu="4000")
        print etree.tostring(el)
        print ""

    def test_render_cham(self):
        print "chameleooon"
        print ""
        print ""
        file = pkg_resources.resource_filename("prambanan", "test/template/template.pt")
        cham = PageTemplate(open(file).read())
        s = cham.render( a="lalal", b=["c", "d"], c=True, width=500, anu="4000")
        print s
        print ""

