import unittest
import os
import subprocess

from StringIO import StringIO
from prambanan.compiler.pytranslator import  translate_file
from prambanan import jsbeautifier

dir = os.path.dirname(os.path.realpath(__file__))
rhino_path = os.path.join(dir, "js.jar")
src_dir = os.path.join(dir, "output")
gen_dir = os.path.join(dir, "output", "gen")
js_dir = os.path.join(dir, "..", "js")
run_js = os.path.join(dir, "run.js")

def create_rhino_args(name):
    args = ["java", "-jar", rhino_path, run_js]
    args.append(os.path.join(js_dir, "lib", "underscore.js"))
    args.append(os.path.join(js_dir, "lib", "backbone.js"))
    args.append(os.path.join(js_dir, "prambanan.js"))
    args.append(os.path.join(gen_dir, name+".js"))
    return args

def create_python_args(name):
    args = ["python"]
    args.append(os.path.join(src_dir, name+".py"))
    return args

def execute(args):
    proc = subprocess.Popen(args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)
    stdout, stderr = proc.communicate()
    print stderr
    return stdout.replace("\r\n", "\n")

js_opt = jsbeautifier.BeautifierOptions()
js_opt.jslint_happy = True

def create_prambanan_config(input_name):
    lines = open(os.path.join(src_dir, input_name), 'r').readlines()
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

def py_to_js(name):
    config = create_prambanan_config(name+".py")
    translate_file(config)
    result = jsbeautifier.beautify(config["output"].getvalue(), js_opt)
    resultname = name+".js"
    with open(os.path.join(gen_dir, resultname), "w") as f:
        f.write(result)



class TestOutput(unittest.TestCase):

    def test_run(self):
        for dirname, dirnames, filenames in os.walk(src_dir):
            for filename in filenames:
                name, ext = os.path.splitext(filename)
                if ext == ".py":
                    print "------------------"
                    print "executing "+filename
                    py_to_js(name)
                    js =  execute(create_rhino_args(name))
                    py =  execute(create_python_args(name))
                    print "js: "
                    print js
                    print "python: "
                    print py
                    self.assertEquals(js, py)



