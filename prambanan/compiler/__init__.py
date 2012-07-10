import prambanan.compiler.astng_patch

from StringIO import StringIO
from exceptions import SyntaxError
from logilab.astng import nodes, builder
from logilab.astng.utils import ASTWalker
import os
import pkg_resources
import logging
from .scopegenerator import ScopeGenerator
from .target import targets
from .utils import ParseError
from ..template import get_provider

import inference

logger = logging.getLogger("prambanan")

class ImportFinder(ASTWalker):

    def __init__(self, modname):
        ASTWalker.__init__(self, self)
        self.imports = []
        self.modname = modname

    def set_context(self, a, b):
        pass

    def visit_from(self, i):
        module = i.modname
        level = i.level
        while level > 0:
            if module == "":
                module = self.modname
            else:
                module = self.modname+"."+module
            level -= 1
        if module not in [self.modname+".native", self.modname+"_native", self.modname]:
            self.imports.append(module)

    def visit_import(self, i):
        for name, asname in i.names:
            importname = name
            if importname != self.modname:
                self.imports.append(importname)

    @staticmethod
    def find_imports(file, modname, import_cache=None):
        results = None
        if import_cache is not None:
            if not import_cache.is_file_changed(file):
                results = import_cache.get_imports(file)
                if results is None:
                    print "ea"

        if results is None:
            tree = builder.ASTNGBuilder().file_build(file)
            finder = ImportFinder(modname)
            finder.walk(tree)
            results =  set(finder.imports)

            if import_cache is not None:
                import_cache.set_imports(file, results)
        return results

    @staticmethod
    def string_find_imports(string):
        tree = builder.ASTNGBuilder().string_build(string)
        finder = ImportFinder("")
        finder.walk(tree)
        return set(finder.imports)

class TemplateFinder(ASTWalker):

    def __init__(self):
        ASTWalker.__init__(self, self)
        self.templates = {}

    def set_context(self, a, b):
        pass

    def visit_callfunc(self, c):
        if inference.infer_qname(c.func) == "prambanan.native.get_template":
            template_type =  inference.ConstEvaluator().visit(c.args[0])
            template_config = inference.ConstEvaluator().visit(c.args[1])
            if not template_type in self.templates:
                self.templates[template_type] = []
            if not template_config in self.templates[template_type]:
                self.templates[template_type].append(template_config)


    @staticmethod
    def find_templates(file, import_cache=None):
        results = None
        if import_cache is not None:
            if not import_cache.is_file_changed(file):
                results = import_cache.get_templates(file)

        if results is None:
            tree = builder.ASTNGBuilder().file_build(file)
            finder = TemplateFinder()
            finder.walk(tree)
            results = finder.templates

            if import_cache is not None:
                import_cache.set_templates(file, results)
        return results

class Module(object):
    def __init__(self, modname, dependencies, templates):
        self.modname = modname

        if dependencies is None:
            dependencies = set()
        if templates is None:
            templates = {}

        self.dependencies = dependencies
        self.templates = templates

    def __str__(self):
        return "Module: %s" % self.modname

class JavascriptModule(Module):
    def __init__(self, paths, modname, dependencies=None, templates=None):
        if isinstance(paths, str):
            paths = [paths]
        self.paths = paths
        super(JavascriptModule, self).__init__(modname, dependencies, templates)

    def files(self):
        for path in self.paths:
            yield ("js", path, self.modname)

class PythonModule(Module):
    def __init__(self, path, modname, import_cache=None, js_deps=None):
        if js_deps is None:
            js_deps = []
        self.js_deps = js_deps
        self.path = path
        super(PythonModule, self).__init__(modname, ImportFinder.find_imports(path, modname, import_cache), TemplateFinder.find_templates(path, import_cache))

    def files(self):
        for path in self.js_deps:
            yield ("js", path, self.modname)
        yield ("py", self.path, self.modname)

__base_js_lib = lambda name: pkg_resources.resource_filename("prambanan", "js/lib/"+name)
__base_js = lambda name: pkg_resources.resource_filename("prambanan", "js/"+name)
__base_py = lambda name: pkg_resources.resource_filename("prambanan", name)

RUNTIME_MODULES = []
RUNTIME_MODULES.append(JavascriptModule([
    __base_js_lib("underscore.js"),
    __base_js_lib("backbone.js"),
    __base_js("prambanan.runtime.js"),
    ], "__prambanan__"))
RUNTIME_MODULES.append(PythonModule(__base_py("__init__.py"), "prambanan"))
RUNTIME_MODULES.append(PythonModule(__base_py("pylib/builtins.py"), "__builtin__"))

class IgnoredFiles(object):

    def __init__(self, dir):
        self.dir = dir
        self.ignored = []
        ignore_file = os.path.join(dir, ".pramignore")
        if os.path.exists(ignore_file):
            with open(ignore_file) as f:
                for line in f.readlines():
                    self.ignored.append(line.strip())

    def is_ignored(self, name):
        abs_path = os.path.join(self.dir, name)

        if name in self.ignored:
            return True

        if os.path.isdir(abs_path):
            dir_init = os.path.join(abs_path, "__init__.py")
            if os.path.exists(dir_init):
                return False
            else:
                return True
        else:
            n, ext = os.path.splitext(name)
            if ext != ".py":
                return True
            if n == "native" or n.endswith("_native"):
                return True
            return False

def walk(top):

    join, isdir = os.path.join, os.path.isdir

    names = os.listdir(top)

    dirs, nondirs = [], []
    ignored = IgnoredFiles(top)
    for name in names:
        if not ignored.is_ignored(name):
            if isdir(join(top, name)):
                dirs.append(name)
            else:
                nondirs.append(name)

    yield top, dirs, nondirs

    for name in dirs:
        new_path = join(top, name)
        for x in walk(new_path):
            yield x

def files_to_modules(files, base_directory, import_cache):
    for file in  files:
        base_name = os.path.basename(file)
        name, ext = os.path.splitext(base_name)
        dir_name = os.path.dirname(os.path.abspath(file))
        rel_dir = os.path.dirname(os.path.relpath(file, base_directory))
        base_modname = ".".join(os.path.normpath(rel_dir).split(os.path.sep))
        if base_modname.startswith("."):
            base_modname = base_modname[1:]
        if name == "__init__":
            modname = base_modname
        else:
            modname = name if base_modname == "" else "%s.%s" % (base_modname, name)
        yield PythonModule(file, modname, import_cache)

def package_to_modules(package, import_cache):
    dir = pkg_resources.resource_filename(package, "")
    base_dir = os.path.join(dir, "..")
    for dirname, dirnames, filenames in  walk(dir):
        abs_files = [os.path.join(dirname, f) for f in filenames]
        for result in files_to_modules(abs_files, base_dir, import_cache):
            yield result

def py_visit_module(self, mod):
    """
    Initial node.
    There is and can be only one Module node.

    """
    self.curr_scope = self.mod_scope

    if not self.bare:
        self.change_buffer(self.HEADER_BUFFER)
        if mod.doc:
            self.write_docstring(self.mod_scope.docstring)

        self.write("(function(%s) {" % self.lib_name)
        self.change_buffer(self.BODY_BUFFER)

        public_identifiers = self.mod_scope.module_all
        not_all_exists = public_identifiers is None
        if not_all_exists:
            public_identifiers = []

    for k, v in self.export_map.items():
        self.mod_scope.declare_variable(k)
        self.write("%s = %s.%s;" % (k, self.lib_name, v))

    for stmt in mod.body:
        if isinstance(stmt, nodes.Assign) and len(stmt.targets) == 1 and\
           isinstance(stmt.targets[0], nodes.Name) and\
           stmt.targets[0].name in ("__all__", "__license__"):
            continue
        """
        if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Str):
            continue # Module docstring
        """

        if not self.bare and not_all_exists:
            for name in self.get_identifiers(stmt):
                if name is not None and not name.startswith("_"):
                    public_identifiers.append(name)

        self.visit(stmt)
        if not isinstance(stmt, nodes.Import) and not isinstance(stmt, nodes.From) and not isinstance(stmt, nodes.Pass):
            self.write_semicolon(stmt)

    if not self.bare:
        self.public_identifiers.extend(public_identifiers)

        get_name = lambda name: name if name not in self.translated_names else self.translated_names[name]
        exported = (self.exe_first_differs(sorted(set(self.public_identifiers)), rest_text=",",
            do_visit=lambda name: self.write("%s: %s" % (name, get_name(name)))))

        self.write("%s.exports('%s',{%s});})(prambanan);" % (self.lib_name, self.modname, exported))

    builtin_var = None
    builtins = set(self.mod_scope.all_used_builtins())
    if len(builtins) > 0:
        builtin_var = self.curr_scope.generate_variable("__builtin__")
        for builtin in builtins:
            if self.modname != "__builtin__" or builtin not in self.public_identifiers:
                self.curr_scope.declare_variable(builtin)

    self.change_buffer(self.HEADER_BUFFER)
    self.write_variables()

    if len(builtins) > 0:
        self.write("%s = %s.import('__builtin__');" %(builtin_var, self.lib_name))
        for builtin in builtins:
            if self.modname != "__builtin__" or builtin not in self.public_identifiers:
                self.write("%s = %s.%s;" %(builtin, builtin_var, builtin))

    for item in self.util_names.values():
        name, value = item
        self.write("%s = %s;" %(name, value))

    self.flush_all_buffer()
    self.curr_scope = None


def translate_string(input, manager,modname="", target=None):
    config = {}
    output = StringIO()
    config["bare"] = True
    config["input_name"] = None
    config["input_lines"] = [input]
    config["output"] = StringIO()
    config["modname"] = modname
    config["use_throw_helper"] = True
    config["warnings"] = False
    config["use_throw_helper"] = False

    try:
        tree = builder.ASTNGBuilder(manager).string_build(input, modname)
    except SyntaxError as e:
        raise ParseError(e.msg, e.lineno, e.offset, True)

    scope_gen = ScopeGenerator(config["modname"], tree)

    direct_handlers = {"module": py_visit_module}
    moo = targets.get_translator(target)(scope_gen.root_scope, direct_handlers, config)
    moo.walk(tree)
    return config["output"].getvalue()


def translate(config, manager):
    try:
        modname = config["modname"]
        tree_modname = "" if modname == "__builtin__" else modname
        tree = builder.ASTNGBuilder(manager).string_build(config["input"], tree_modname, config["input_path"])
        scope_gen = ScopeGenerator(modname, tree)
        scope_gen.visit(tree)

        visit_module = config.get("visit_module", py_visit_module)

        direct_handlers = {"module": visit_module}
        target = config.get("target", None)
        moo = targets.get_translator(target)(scope_gen.root_scope, direct_handlers, config)
        moo.walk(tree)
        return scope_gen.root_scope.imported_modules()
    except ParseError as e:
        e.input_lines = config["input_lines"]
        e.input_name = config["input_name"]
        raise e
    except SyntaxError as e:

        raise ParseError(e.msg, e.lineno, e.offset, True, config["input_lines"], config["input_name"])
