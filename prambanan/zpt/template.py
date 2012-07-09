import pkg_resources

from prambanan.zpt.cmd import template_changed, generate, get_imports
from prambanan.template import Template

class LazyPageTemplate(object):

    def __init__(self, package, filename):
        self.package = package
        self.filename = filename

    def render(self, el, model, **vars):
        from prambanan.zpt import PageTemplate
        from prambanan.zpt.compiler.ptparser import PTParser

        file = pkg_resources.resource_filename(self.package, self.filename)
        pt = PTParser(file)
        compiled = compile(pt.code, self.filename, "exec")
        print pt.code
        env = {}
        exec(compiled, env)
        return PageTemplate(env["render"]).render(el, model, **vars)

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

