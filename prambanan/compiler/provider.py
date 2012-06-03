import pkg_resources

class PrambananProvider(object):

    def __init__(self, name):
        self.name = name

    def get_overridden_types(self):
        """
        "return directory containing <qname>:<"Function"|"Class">
        """
        pass

    def get_modules(self):
        """
        return list containing <module>:moduleitem
        """
        pass

def all_providers():
    providers = []
    eps = list(pkg_resources.iter_entry_points('prambanan.provider'))
    for entry in eps:
        provider_class = entry.load()
        provider = provider_class(entry.name)
        providers.append(provider)
    return providers
