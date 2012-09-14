from prambanan.compiler import *
from prambanan.compiler.library import PrambananLibrary
from os.path import *
from pkg_resources import resource_filename
import pkg_resources

pylib_dir = resource_filename("prambanan", "pylib/")

class MainPrambananLibrary(PrambananLibrary):
    def __init__(self, *args):
        super(MainPrambananLibrary, self).__init__(*args)
        self.modules = [
            PythonModule(join(pylib_dir, "math.py"), "math", self.import_cache),
            PythonModule(join(pylib_dir, "time.py"), "time", self.import_cache),
            PythonModule(join(pylib_dir, "datetime.py"), "datetime", self.import_cache),
            PythonModule(resource_filename("prambanan", "zpt/__init__.py"), "prambanan.zpt", self.import_cache),
            ]

    def get_overridden_types(self):
        return {}

    def get_modules(self):
        return self.modules[:]
