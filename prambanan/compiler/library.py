import pkg_resources

class PrambananLibrary(object):

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

def all_libraries():
    providers = []
    eps = list(pkg_resources.iter_entry_points('prambanan.library'))
    for entry in eps:
        provider_class = entry.load()
        provider = provider_class(entry.name)
        providers.append(provider)
    return providers