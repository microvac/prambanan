import unittest
import os
import subprocess
import pkg_resources

from StringIO import StringIO
from prambanan.compiler import translate
from prambanan import jsbeautifier

js_opt = jsbeautifier.BeautifierOptions()
js_opt.jslint_happy = True

class OutputTester(object):

    dir = pkg_resources.resource_filename("prambanan", "test/")
    js_dir = pkg_resources.resource_filename("prambanan", "js/")

    rhino_path = os.path.join(dir, "js.jar")
    run_js = os.path.join(dir, "run.js")

    def __init__(self, src_dir, included_js=[]):
        self.src_dir = src_dir
        self.included_js = included_js
        self.gen_dir = os.path.join(src_dir, "gen")

    def execute(self, args):
        proc = subprocess.Popen(args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        stdout, stderr = proc.communicate()
        print stderr
        return stdout.replace("\r\n", "\n")

    def create_rhino_args(self, name):
        args = ["java", "-jar", self.rhino_path, self.run_js]
        args.append(os.path.join(self.js_dir, "lib", "underscore.js"))
        args.append(os.path.join(self.js_dir, "lib", "backbone.js"))
        args.append(os.path.join(self.js_dir, "prambanan.js"))
        for included_js in self.included_js:
            args.append(included_js)
        args.append(os.path.join(self.gen_dir, name+".js"))
        return args

    def create_python_args(self, name):
        args = ["python"]
        args.append(os.path.join(self.src_dir, name+".py"))
        return args

    def py_to_js(self, name):
        config = self.create_prambanan_config(name+".py")
        translate(config)
        result = jsbeautifier.beautify(config["output"].getvalue(), js_opt)
        result_name = name+".js"
        with open(os.path.join(self.gen_dir, result_name), "w") as f:
            f.write(result)

    def create_prambanan_config(self, input_name):
        lines = open(os.path.join(self.src_dir, input_name), 'r').readlines()
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

    def run(self):
        for dirname, dirnames, filenames in os.walk(self.src_dir):
            for filename in filenames:
                name, ext = os.path.splitext(filename)
                if ext == ".py":
                    print "------------------"
                    print "executing "+filename
                    self.py_to_js(name)
                    js =  self.execute(self.create_rhino_args(name))
                    py =  self.execute(self.create_python_args(name))
                    yield (js, py)
