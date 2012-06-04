from logilab.astng.manager import ASTNGManager
from prambanan.compiler import RUNTIME_MODULES
from prambanan.compiler.library import all_libraries

import pickle
import os

class PrambananManager(ASTNGManager):

    def __init__(self, modules, file_stats_file=None):
        super(PrambananManager, self).__init__()
        self.mod_files ={}

        self.file_stats_file = file_stats_file
        if file_stats_file is not None:
            if os.path.exists(file_stats_file):
                self.file_stats = pickle.load(open(file_stats_file))
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
        if modname in self.mod_files:
            return self.mod_files[modname]

        #todo fix this
        prefixed_results = []
        for name in self.mod_files:
            if name == modname or ("." in modname and modname.rsplit(".", 1)[0] == name):
                prefixed_results.append(name)
        if len(prefixed_results) > 0:
            key =  max(prefixed_results, key=lambda x: len(x))
            return self.mod_files[key]

        return super(PrambananManager, self).file_from_module_name(modname, contextfile)

    def is_file_changed(self, file):
        if self.file_stats is None:
            return True

        file_mtime = os.stat(file).st_mtime
        prev_mtime = self.file_stats[file] if file in self.file_stats  else 0

        if file_mtime > prev_mtime:
            self.file_stats[file] = file_mtime
            with open(self.file_stats_file, "w") as f:
                pickle.dump(self.file_stats, f)
            return True

        return False

    def add_module(self, module):
        for type, file, modname in module.files():
            if type == "py":
                self.mod_files[modname] = file


