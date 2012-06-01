from logilab.astng.manager import ASTNGManager
from prambanan.compiler import RUNTIME_MODULES
from prambanan.compiler.provider import all_providers

class PrambananManager(ASTNGManager):

    def __init__(self, modules):
        super(PrambananManager, self).__init__()
        self.mod_files ={}

        providers = all_providers()
        providers_modules = dict([ (n,m) for p in providers for n,m in p.get_modules().items()])
        all_modules = providers_modules.values() + modules + RUNTIME_MODULES

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

    def add_module(self, module):
        for type, file, modname in module.files():
            if type == "py":
                self.mod_files[modname] = file

