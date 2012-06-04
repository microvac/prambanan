import pkg_resources

from cmd import generate
from ..template import Template

class LazyPageTemplate(object):

    def __init__(self, package, filename):
        self.package = package
        self.filename = filename

    def render(self, el, **vars):
        from prambanan.zpt import PageTemplate
        from prambanan.zpt.compiler.ptparser import PTParser

        file = pkg_resources.resource_filename(self.package, self.filename)
        pt = PTParser(file)
        compiled = compile(pt.code, self.filename, "exec")
        env = {}
        exec(compiled, env)
        return PageTemplate(env["render"]).render(el, **vars)

class ZPTTemplate(Template):

    def get(self, template_config):
        package, filename = template_config
        return LazyPageTemplate(package, filename)

    def compile(self, translate_args, output_manager, manager, template_configs):
        generate(translate_args, output_manager, manager, template_configs)

    def template_dependencies(self):
        return ["prambanan.zpt"]

