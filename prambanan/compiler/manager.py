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

        libraries = all_libraries(self)
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
        prev_mtime = self.file_stats[file]["st_mtime"] if file in self.file_stats  else 0

        if file_mtime > prev_mtime:
            return True

        return False

    def mark_file_processed(self, file):
        if self.cache_file is None:
            return

        file_mtime = os.stat(file).st_mtime
        prev_imports = None
        prev_templates = None
        if file in self.file_stats:
            prev_imports = self.file_stats[file]["imports"]
            prev_templates = self.file_stats[file]["templates"]
        self.file_stats[file] = {"st_mtime": file_mtime, "imports": prev_imports, "templates": prev_templates}
        with open(self.cache_file, "w") as f:
            pickle.dump(self.file_stats, f)

    def set_imports(self, file, imports):
        if self.cache_file is None:
            return
        file_mtime = os.stat(file).st_mtime
        file_stat = self.file_stats.get(file, self.empty_entry(file, file_mtime))
        file_stat["imports"] = imports
        self.file_stats[file] = file_stat
        with open(self.cache_file, "w") as f:
            pickle.dump(self.file_stats, f)

    def get_imports(self, file):
        if self.cache_file is None:
            return None
        if file in self.file_stats:
            return  self.file_stats[file]["imports"]
        return None

    def set_templates(self, file, templates):
        if self.cache_file is None:
            return
        file_mtime = os.stat(file).st_mtime
        file_stat = self.file_stats.get(file, self.empty_entry(file, file_mtime))
        file_stat["templates"] = templates
        self.file_stats[file] = file_stat
        with open(self.cache_file, "w") as f:
            pickle.dump(self.file_stats, f)

    def get_templates(self, file):
        if self.cache_file is None:
            return None
        if file in self.file_stats:
            return  self.file_stats[file]["templates"]
        return None

    def empty_entry(self, file, file_mtime):
        return {"st_mtime": file_mtime, "imports": None, "templates": None}


    def add_module(self, module):
        for type, file, modname in module.files():
            if type == "py":
                self.mod_files[modname] = file


