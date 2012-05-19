import ast
from . import ParseError


class Scope(object):
    """
    First-pass context parser. Builds an execution context for type inference
    and captures docstrings.

    """
    BUILTINS_FUNC = [
        "bool", "int", "str", "float", "basestring", "unicode",
        "min", "max", "abs", "round",
        "all", "any", "reversed", "sorted", "len", "set", "dict", "list",
        "filter", "map", "reduce",
        "callable", "super", "type", "tuple", "__import__", "isinstance", "issubclass",
        "range", "xrange", "iter", "enumerate",
        "print",
        "None"
        ]

    BUILTINS_CLASS = [
        "object",
        "BaseException",
            "Exception",
                "StandardError",
                     "AtributeError", "TypeError", "ValueError", "NameError", "SystemError"
                    "LookupError",
                            "IndexError", "KeyError",
                    "ArithmeticError",
                        "ZeroDivisionError"
                    "RuntimeError",
                        "NotImplementedError"
    ]

    def __init__(self, type, name, parent = None):
        """
        Parse the node as a new context. The parent must be another context
        object. Only Module, Class, Method and Function nodes are allowed.

        """
        self.module_license = ""
        self.module_all = None

        self.type = type
        self.name = name
        self.parent = parent

        self.generators = {}
        self.identifiers = {}
        self.known_types = {}

        self.undeclared_variables = []
        self.variables = [] # Holds declared local variables (filled on second pass)
        self.global_variables = []
        self.imports = {}
        self.used_builtins = []
        self.list_comp_id = 0



    def all_imports(self):
        if self.parent is not None:
            return dict(self.imports.items() + self.parent.all_imports().items())
        return self.imports

    def all_used_builtins(self):
        builtins = self.used_builtins[:]
        for id, child in self.identifiers.items():
            builtins.extend(child.all_used_builtins())
        return builtins


    def use_builtin(self, name):
        if not name in self.used_builtins:
            self.used_builtins.append(name)

    def check_builtin_usage(self, name):
        if name in self.BUILTINS_FUNC or name in self.BUILTINS_CLASS:
            self.use_builtin(name)
            return True
        return False

    def generate_list_comp_id(self):
        result = "list-comp-%d" % self.list_comp_id
        self.list_comp_id += 1
        return result


    def child(self, identifier):
        """
        Get a named child context.

        """
        if self.identifiers.has_key(identifier):
            return self.identifiers[identifier]
        return None

    def lookup(self, identifier):
        """
        Get a context in this or the parents context.
        Jumps over Class contexts.

        """
        if self.type != "Class":
            if self.identifiers.has_key(identifier):
                return self.identifiers[identifier]
        if self.parent is not None:
            return self.parent.lookup(identifier)
        return None

    def class_context(self):
        """
        Return the topmost class context (useful to get the context for `self`).

        """
        if self.type == "Class":
            return self
        elif self.parent is None:
            return None
        return self.parent.class_context()

    def register_variable_type(self, name, t):
        self.known_types[name] = t

    def lookup_variable_type(self, name):
        if self.known_types.has_key(name):
            return self.known_types[name]
        if self.parent is not None:
            return self.parent.lookup_variable_type(name)
        return None

    def is_variable_free(self, name):
        if name in self.undeclared_variables or name in self.global_variables or name in self.variables:
            return False
        if self.parent is not None:
            return self.parent.is_variable_free(name)
        return True

    def declare_variable(self, name, declared=True):
        """
        Returns False if the variable is already declared and True if not.

        """
        if (not name in self.undeclared_variables) and (not name in self.global_variables) and (not name in self.variables):
            if declared:
                self.variables.append(name)
            else:
                self.undeclared_variables.append(name)

    def generate_variable(self, base_name, declared=True):
        name = None
        while True:
            id = self.get_generator_id(base_name)
            if id == 0:
                name = base_name
            else:
                name = "%s%d" % (base_name, id)
            if self.is_variable_free(name):
                self.declare_variable(name, declared)
                break
        return name

    def get_generator_id(self, base_name):
        if base_name not in self.generators:
            self.generators[base_name] = 0
        i = self.generators[base_name]
        self.generators[base_name] = i + 1
        return i

