import unittest
import os
import subprocess
import output_tester

from StringIO import StringIO
from prambanan.compiler import translate
from prambanan import jsbeautifier

dir = os.path.dirname(os.path.realpath(__file__))
src_dir = os.path.join(dir, "output")

@output_tester.directory_tester(src_dir, print_output=True)
class TestOutput(unittest.TestCase):
    pass



