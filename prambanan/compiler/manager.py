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
                self.file_stats = {
                    "processed": {},
                    "imports": {},
                    "templates": {},
                }
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

        result =  super(PrambananManager, self).file_from_module_name(modname, contextfile)

        return result


    def is_file_changed(self, file):
        if self.cache_file is None:
            return True

        file_mtime = os.stat(file).st_mtime
        prev_mtime = self.file_stats["processed"][file] if file in self.file_stats["processed"]  else 0

        if file_mtime > prev_mtime:
            return True

        return False

    def mark_file_processed(self, file):
        if self.cache_file is None:
            return

        file_mtime = os.stat(file).st_mtime
        self.file_stats["processed"][file] = file_mtime
        with open(self.cache_file, "w") as f:
            pickle.dump(self.file_stats, f)

    def set_imports(self, file, imports):
        if self.cache_file is None:
            return
        file_mtime = os.stat(file).st_mtime
        self.file_stats["imports"][file] = (file_mtime, imports)
        with open(self.cache_file, "w") as f:
            pickle.dump(self.file_stats, f)

    def get_imports(self, file):
        if self.cache_file is None:
            return None

        if file not in self.file_stats["imports"]:
            return None

        save_mtime, imports = self.file_stats["imports"][file]
        file_mtime = os.stat(file).st_mtime
        if file_mtime > save_mtime:
            return None

        return imports

    def set_templates(self, file, templates):
        if self.cache_file is None:
            return
        file_mtime = os.stat(file).st_mtime
        self.file_stats["templates"][file] = (file_mtime, templates)
        with open(self.cache_file, "w") as f:
            pickle.dump(self.file_stats, f)

    def get_templates(self, file):
        if self.cache_file is None:
            return None

        if file not in self.file_stats["templates"]:
            return None

        save_mtime, imports = self.file_stats["templates"][file]
        file_mtime = os.stat(file).st_mtime
        if file_mtime > save_mtime:
            return None

        return imports

    def add_module(self, module):
        for type, file, modname in module.files():
            if type == "py":
                self.mod_files[modname] = file


