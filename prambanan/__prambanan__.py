from prambanan.compiler import *
from prambanan.compiler.provider import PrambananProvider
from os.path import *
from pkg_resources import resource_filename
import pkg_resources

pylib_dir = resource_filename("prambanan", "pylib/")

class MainPrambananProvider(PrambananProvider):
    modules = [
        PythonModule(join(pylib_dir, "math.py"), "math"),
        PythonModule(join(pylib_dir, "time.py"), "time"),
        PythonModule(join(pylib_dir, "datetime.py"), "datetime"),
        PythonModule(resource_filename("prambanan", "zpt/__init__.py"), "prambanan.zpt"),
    ]

    def get_overridden_types(self):
        return {}

    def get_modules(self):
        return self.modules[:]
