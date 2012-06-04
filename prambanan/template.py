import pkg_resources

class TemplateProvider(object):
    def get_template(self, template_config):
        pass
    def compile_template(self, template_config, **kwargs):
        pass

def all_providers():
    providers = {}
    eps = list(pkg_resources.iter_entry_points('prambanan.template'))
    for entry in eps:
        provider_class = entry.load()
        provider = provider_class()
        providers[entry.name] = provider
    return providers

