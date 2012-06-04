import unittest
from prambanan.pramlib import MainPrambananLibrary
from prambanan.compiler import ImportFinder

class TestImportFinder(unittest.TestCase):

    def test_datetime(self):
        provider = MainPrambananLibrary("prambanan")
        for module in provider.get_modules():
            if module.modname == "datetime":
                dt = module
                imps = ImportFinder.find_imports(dt.path, dt.modname)
                print imps
