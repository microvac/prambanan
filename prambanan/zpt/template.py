import os
import pkg_resources
from prambanan.compiler import TemplateModule

from prambanan.zpt.cmd import template_changed, generate, get_imports
from prambanan.template import Template

class LazyPageTemplate(object):

    def __init__(self, package, filename):
        self.package = package
        self.filename = filename

    def render(self, el, model, vars=None):
        from prambanan.zpt import PageTemplate
        from prambanan.zpt.compiler.ptparser import PTParser

        file = pkg_resources.resource_filename(self.package, self.filename)
        pt = PTParser(file)
        compiled = compile(pt.code, self.filename, "exec")
        env = {}
        exec(compiled, env)
        return PageTemplate(env["render"]).render(el, model, vars)

class ZPTTemplate(Template):

    def get(self, template_config):
        package, filename = template_config
        return LazyPageTemplate(package, filename)

    def compile(self, translate_args, output_manager, manager, template_configs):
        generate(translate_args, output_manager, manager, template_configs)

    def get_imports(self, template_config):
        package, path = template_config
        return get_imports(package, path)

    def changed(self, output_manager, manager, template_configs):
        return template_changed(output_manager, manager, template_configs)

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
            return False
        else:
            n, ext = os.path.splitext(name)
            if ext != ".pt":
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

def files_to_modules(package, package_absolute_files, import_cache):
    for file in  package_absolute_files:
        yield TemplateModule("zpt", (package, file), import_cache)

def templates_to_modules(package, dir, import_cache):
    base_dir = pkg_resources.resource_filename(package, dir)
    package_abs_dir = dir.replace("\\", "/")
    for dirname, dirnames, filenames in  walk(base_dir):
        diff_dir = os.path.relpath(dirname, base_dir).replace("\\", "/")
        def convert(f):
            if diff_dir == ".":
                joins = [package_abs_dir, f]
            else:
                joins = [package_abs_dir, diff_dir, f]
            return "/".join(joins)
        package_abs_files = [convert(f) for f in filenames]
        for result in files_to_modules(package, package_abs_files, import_cache):
            yield result
