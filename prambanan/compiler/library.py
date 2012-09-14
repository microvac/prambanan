import pkg_resources

class PrambananLibrary(object):

    def __init__(self, name, import_cache):
        self.name = name
        self.import_cache = import_cache

    def get_overridden_types(self):
        """
        "return directory containing <qname>:<"Function"|"Class">
        """
        return {}


    def get_modules(self):
        """
        return list containing <module>:moduleitem
        """
        pass

def all_libraries(import_cache=None):
    providers = []
    import datetime
    start = datetime.datetime.now()
    eps = list(pkg_resources.iter_entry_points('prambanan.library'))
    for entry in eps:
        provider_class = entry.load()
        provider = provider_class(entry.name, import_cache)
        providers.append(provider)
        print datetime.datetime.now() - start
    print datetime.datetime.now() - start
    return providers
