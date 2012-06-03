import unittest
from chameleon.zpt.template import PageTemplate
import os
from lxml import etree
import pkg_resources
from prambanan.zpt import TemplateRegistry
import time

dir = os.path.dirname(os.path.realpath(__file__))

zpt_dir = os.path.join(dir, "template")
gen_dir = os.path.join(zpt_dir, "gen")

#init prambanan
registry = TemplateRegistry()
registry.register_py("prambanan", "test/template/template.pt")
pt = registry.get("prambanan", "test/template/template")

#init chameleon
file = pkg_resources.resource_filename("prambanan", "test/template/template.pt")
cham = PageTemplate(open(file).read())

def render_prambanan(i):
    el = etree.Element("div")
    el = pt.render(el, a="lalal", b=["c", "d"], c=True, width=i, anu="4000")
    return etree.tostring(el)

def render_cham(i):
    return cham.render( a="lalal", b=["c", "d"], c=True, width=i, anu="4000")

print render_prambanan(23)
print render_cham(23)

start = time.time()
for i in xrange(0, 10000):
    s = render_cham(i)
print 'chameleon time: %f' % (time.time() - start)

start = time.time()
for i in xrange(0, 10000):
    s = render_prambanan(i)
print 'prambanan time: %f' % (time.time() - start)

start = time.time()
for i in xrange(0, 10000):
    s = render_cham(i)
print 'chameleon time: %f' % (time.time() - start)

