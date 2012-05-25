import unittest
import os
import subprocess

from StringIO import StringIO
from prambanan.compiler import translate
from prambanan import jsbeautifier
from prambanan.test.output_tester import OutputTester

dir = os.path.dirname(os.path.realpath(__file__))
src_dir = os.path.join(dir, "output")



class TestOutput(unittest.TestCase):

    def test_run(self):
        tester = OutputTester(src_dir)
        for js, py in tester.run():
            print "js: "
            print js
            print "python: "
            print py
            self.assertEquals(js, py)



