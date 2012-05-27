from logilab.astng import builder
from logilab.astng.utils import ASTWalker

class ImportFinder(ASTWalker):

    def __init__(self, namespace):
        ASTWalker.__init__(self, self)
        self.imports = []
        self.namespace = namespace

    def set_context(self, a, b):
        pass

    def visit_from(self, i):
        module = i.modname
        level = i.level
        while level > 0:
            if module == "":
                module = self.namespace
            else:
                module = self.namespace+"."+module
            level -= 1
        if module not in [self.namespace+".native", self.namespace+"_native", self.namespace]:
            self.imports.append(module)

    def visit_import(self, i):
        for name, asname in i.names:
            importname = name
            if importname != self.namespace:
                self.imports.append(importname)

    @staticmethod
    def find_imports(file, namespace):
        tree = builder.ASTNGBuilder().file_build(file)
        finder = ImportFinder(namespace)
        finder.walk(tree)
        return set(finder.imports)



