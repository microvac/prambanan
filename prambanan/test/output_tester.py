import unittest
import os
import subprocess
import pkg_resources

from StringIO import StringIO
from prambanan.cmd import generate_runtime, create_args, translate_parser,  generate, generate_parser
from prambanan.compiler import translate, files_to_modules
from prambanan import jsbeautifier
from prambanan.compiler.manager import PrambananManager

js_opt = jsbeautifier.BeautifierOptions()
js_opt.jslint_happy = True

class OutputTester(object):

    dir = pkg_resources.resource_filename("prambanan", "test/")

    rhino_path = os.path.join(dir, "rhino.jar")
    run_js = os.path.join(dir, "run_rhino.js")

    def __init__(self, src_dir):
        self.src_dir = src_dir
        self.gen_dir = os.path.join(src_dir, "gen")
        self.runtime_file = os.path.join(self.gen_dir, "__runtime__.js")
        self.manager = PrambananManager([])
        with open(self.runtime_file, "w") as f:
            generate_runtime(create_args(translate_parser, output=f), self.manager)

    def execute(self, args):
        proc = subprocess.Popen(args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        stdout, stderr = proc.communicate()
        print stderr
        return stdout.replace("\r\n", "\n")

    def create_rhino_args(self, name):
        args = ["java", "-jar", self.rhino_path, self.run_js]
        args.append(self.runtime_file)
        args.append(os.path.join(self.gen_dir, name+".js"))
        return args

    def create_python_args(self, name):
        args = ["python"]
        args.append(os.path.join(self.src_dir, name+".py"))
        return args

    def py_to_js(self, name):
        result_name = name+".js"
        with open(os.path.join(self.gen_dir, result_name), "w") as f:
            translate_args = create_args(generate_parser, import_warning=True, generate_imports=True, output=f)
            generate(translate_args, self.manager, files_to_modules([os.path.join(self.src_dir, name+".py")], self.src_dir))

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

def make_test_method(tester, name, print_output):
    def result(self):
        print "------------------"
        print "executing "+name
        tester.py_to_js(name)
        js =  tester.execute(tester.create_rhino_args(name))
        py =  tester.execute(tester.create_python_args(name))
        if print_output:
            print "javascript"
            print js
            print "python"
            print py
        self.assertEquals(js, py)
    return result

def make_setup_method(tester, name, print_output):
    def result(self):
        print "------------------"
        print "executing "+name
        tester.py_to_js(name)
        js =  tester.execute(tester.create_rhino_args(name))
        py =  tester.execute(tester.create_python_args(name))
        if print_output:
            print "javascript"
            print js
            print "python"
            print py
        self.assertEquals(js, py)
    return result

def directory_tester(src_dir, print_output=False, files=None):
    tester = OutputTester(src_dir)
    def dec(cls):
        if src_dir is not None:
            for dirname, dirnames, filenames in os.walk(src_dir):
                for filename in filenames:
                    name, ext = os.path.splitext(filename)
                    if ext == ".py":
                        if files is None or name in files:
                            setattr(cls, "test_file_"+name,  make_test_method(tester, name, print_output))
        return cls
    return dec

