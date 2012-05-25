import unittest
import os
from StringIO import StringIO
from prambanan.compiler import translate

from prambanan import jsbeautifier

dir = os.path.dirname(os.path.realpath(__file__))

bare_dir = os.path.join(dir, "bare")
result_dir = os.path.join(dir, "result")

class TestExpression(unittest.TestCase):

    def create_config(self, input_name):
        lines = open(os.path.join(bare_dir, input_name), 'r').readlines()
        config = {}
        output = StringIO()
        config["input"] = StringIO("".join(lines)).read()
        config["bare"] = False
        config["input_name"] = input_name
        config["input_lines"] = lines
        config["output"] = StringIO()
        config["namespace"] = ""
        config["use_throw_helper"] = True
        config["warnings"] = []
        return config


    def test_bare(self):
        js_opt = jsbeautifier.BeautifierOptions()
        js_opt.jslint_happy = True
        for dirname, dirnames, filenames in os.walk(bare_dir):
            for filename in filenames:
                name, ext = os.path.splitext(filename)
                if ext == ".py":
                    print "processing %s.py" % name
                    config = self.create_config(filename)
                    translate(config)
                    result = jsbeautifier.beautify(config["output"].getvalue(), js_opt)
                    resultname = name+".js"
                    with open(os.path.join(result_dir, resultname), "w") as f:
                        f.write(result)



