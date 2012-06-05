from logilab.astng.manager import ASTNGManager
from prambanan.compiler import RUNTIME_MODULES
from prambanan.compiler.library import all_libraries

import pickle
import os

class PrambananManager(ASTNGManager):

    def __init__(self, modules, cache_file=None):
        super(PrambananManager, self).__init__()
        self.mod_files ={}

        self.cache_file = cache_file
        if cache_file is not None:
            if os.path.exists(cache_file):
                self.file_stats = pickle.load(open(cache_file))
            else:
                self.file_stats = {}
        else:
            self.file_stats = None

        libraries = all_libraries()
        libraries_modules = [ m for l in libraries for m in l.get_modules()]
        all_modules = libraries_modules + modules + RUNTIME_MODULES

        for module in all_modules:
            for type, file, modname in module.files():
                if type == "py":
                    self.mod_files[modname] = file

    def file_from_module_name(self, modname, contextfile):
        if modname != "__builtin__":
            if modname in self.mod_files:
                return self.mod_files[modname]

        return super(PrambananManager, self).file_from_module_name(modname, contextfile)

    def is_file_changed(self, file):
        if self.cache_file is None:
            return True

        file_mtime = os.stat(file).st_mtime
        prev_mtime = self.file_stats[file] if file in self.file_stats  else 0

        if file_mtime > prev_mtime:
            return True

        return False

    def mark_file_processed(self, file):
        if self.cache_file is None:
            return

        file_mtime = os.stat(file).st_mtime
        self.file_stats[file] = file_mtime
        with open(self.cache_file, "w") as f:
            pickle.dump(self.file_stats, f)

    def add_module(self, module):
        for type, file, modname in module.files():
            if type == "py":
                self.mod_files[modname] = file


