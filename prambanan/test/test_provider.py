import unittest
from prambanan.compiler.library import all_libraries
from prambanan.cmd import walk_imports

class TestProvider(unittest.TestCase):

    def test_all_providers(self):
        providers = all_libraries()
        self.assertGreater(len(providers), 0)
        for provider in providers:
            self.assertIsNotNone(provider.get_modules())
            self.assertIsNotNone(provider.get_overridden_types())


    def test_walk_imports(self):
        providers = all_libraries()
        modules = {}
        for provider in providers:
            modules.update(dict([(m.modname, m) for m in provider.get_modules()]))
        print walk_imports(["colander"], modules).keys()


