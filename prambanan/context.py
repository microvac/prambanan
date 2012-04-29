import ast
from prambanan import ParseError

class Writer(object):
    def __init__(self, default_buffer, buffers):
        self.buffers = buffers
        self.buffer = default_buffer
        self.indent_level = 0

    def change_buffer(self, name):
        self.buffer = self.buffers[name]

    def write(self, s):
        self.buffer.append(s)

    def indent(self, updown = True):
        if updown:
            self.indent_level += 1
        else:
            self.indent_level -= 1


class Context(ast.NodeVisitor):
    """
    First-pass context parser. Builds an execution context for type inference
    and captures docstrings.

    """
    BUILTINS_FUNC = [
        "bool", "int", "str", "float", "basestring", "unicode",
        "min", "max", "abs", "round",
        "all", "any", "reversed", "sorted", "len",
        "filter", "map", "reduce",
        "callable", "super", "type", "tuple", "__import__", "isinstance", "issubclass",
        "range", "xrange", "iter", "enumerate",
        "print",
        "None"
        ]

    a = LookupError

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

    def __init__(self, namespace, node, buffer_names, parent = None):
        """
        Parse the node as a new context. The parent must be another context
        object. Only Module, Class, Method and Function nodes are allowed.

        """
        self.docstring = ""
        self.module_license = ""
        self.module_all = None
        self.node = node
        self.generators = {}
        self.params = []
        if node.__class__.__name__ == "FunctionDef":
            if parent.type == "Class":
                self.type = "Method"
            else:
                self.type = "Function"
            self.name = node.name
            for arg in node.args.args:
                self.params.append(arg.id)
            self.__get_docstring()
        elif node.__class__.__name__ == "ClassDef":
            self.type = "Class"
            self.name = node.name
            self.__get_docstring()
        elif node.__class__.__name__ == "Module":
            self.type = "Module"
            self.name = "(Module)"
            self.__get_docstring()
        elif node.__class__.__name__ == "ListComp":
            self.type = "ListComp"
            self.name = self.node.name
        else:
            raise ValueError("Only Module, ClassDef and FunctionDef nodes are allowed")

        self.parent = parent
        self.identifiers = {}
        self.known_types = {}
        self.variables = [] # Holds declared local variables (filled on second pass)
        self.globar_variables = []
        self.imports = {}
        self.namespace = namespace
        self.used_builtins = []
        self.list_comp_id = 0

        self.visit_If = self.visit_body
        self.visit_ExceptHandler = self.visit_body

        buffers = {}
        for buffer_name in buffer_names:
            buffers[buffer_name] = []

        self.__buffer_names = buffer_names
        self.writer = Writer(buffers[buffer_names[0]], buffers)

        if self.type != "ListComp":
            self.visit_body(node)

    def visit_func_or_class(self, node):
        if isinstance(node, ast.ListComp):
            node.name = self.generate_list_comp_id()

        if self.identifiers.has_key(node.name):
            old_ctx = self.identifiers[node.name]
            raise ParseError("%s identifier '%s' at line %d is illegaly overwritten" % (
                old_ctx.type,
                node.name,
                old_ctx.node.lineno),
                node.lineno,
                node.col_offset
                )
        self.identifiers[node.name] = Context(self.namespace, node, self.__buffer_names , self)

    def visit_ClassDef(self, c):
        self.declare_variable(c.name)
        bases = filter(lambda b: not isinstance(b, ast.Name) or b.id != "object", c.bases)
        if len(bases) == 0:
            self.use_builtin("object")
        self.visit_func_or_class(c)

    def visit_FunctionDef(self, c):
        self.declare_variable(c.name)
        self.visit_func_or_class( c)

    def all_imports(self):
        if self.parent is not None:
            return dict(self.imports.items() + self.parent.all_imports().items())
        return self.imports

    def all_used_builtins(self):
        builtins = self.used_builtins[:]
        for id, child in self.identifiers.items():
            builtins.extend(child.all_used_builtins())
        return builtins

    def visit_ListComp(self, lc):
        """
        [expr for item if expr in lists] ->
            (function(){
                var _i, _len, _results;
                _results = []
            })();
        """
        for f in lc.generators:
            if isinstance(f, ast.Name):
                self.declare_variable(f.target.id)
            elif isinstance(f, ast.Tuple):
                for elt in f.target.elts:
                    self.declare_variable(elt.id)
        self.visit_func_or_class(lc)

    def use_builtin(self, name):
        if not name in self.used_builtins:
            self.used_builtins.append(name)

    def check_builtin_usage(self, name):
        if name in self.BUILTINS_FUNC or name in self.BUILTINS_CLASS:
            self.use_builtin(name)
            return True
        return False

    def visit_ImportFrom(self, i):
        """
        from module import itema, itemb ->
            module1 = __import__('module'); itema = module1.itema; itemb = module.itemb;
        """
        self.use_builtin("__import__")
        module = i.module
        if i.level == 1:
            if module is None:
                module = self.namespace
            else:
                module = self.namespace+"."+module
        for name in i.names:
            varname = name.asname if name.asname else name.name
            self.declare_variable(varname)
            self.imports[varname] = (module, name.name)

    def visit_Import(self, i):
        """
        import module -> module = __import__(module)
        import namespace.module -> namespace = __import__(namespace)
        import namespace.module as alias -> alias = __import__(namespace.module)
        """
        first = True
        self.use_builtin("__import__")
        for name in i.names:
            importname = name.name
            varname = name.name
            if name.asname:
                varname = name.asname
            else:
                if "." in importname:
                    importname = importname[0:importname.find(".")]
                    varname = importname
            self.declare_variable(varname)
            self.imports[importname] =  (importname, None)

    def visit_Print(self, p):
        """
        Translate print "aa" to print("aa")

        """

        self.use_builtin("print")

    def visit_Call(self, node):
        for arg in node.args:
            self.visit(arg)

    def visit_TryExcept(self, node):
        self.visit_body(node)
        for handler in  node.handlers:
            if(handler.name is not None):
                self.declare_variable(handler.name.id)
            self.visit_body(handler)

    def visit_Global(self, g):
        for name in g.names:
            self.globar_variables.append(g)

    def visit_While(self, w):
        self.visit_body(w)

    def visit_Expr(self, expr):
        self.visit(expr.value)

    def generate_list_comp_id(self):
        result = "list-comp-%d" % self.list_comp_id
        self.list_comp_id += 1
        return result

    def visit_body(self, node):
        for stmt in node.body:
            self.visit(stmt)
        for stmt in getattr(node, "orelse", []):
            self.visit(stmt)

    def visit_Assign(self, stmt):
        if self.type == "Module":
            if len(stmt.targets) == 1 and isinstance(stmt.targets[0], ast.Name):
                if stmt.targets[0].id == "__all__":
                    if not isinstance(stmt.value, ast.List):
                        raise ParseError("Value of `__all__` must be a list expression",stmt.lineno, stmt.col_offset)
                    self.module_all = []
                    for expr in stmt.value.elts:
                        if not isinstance(expr, ast.Str):
                            raise ParseError("All elements of `__all__` must be strings", expr.lineno, expr.col_offset)
                        self.module_all.append(expr.s)
                elif stmt.targets[0].id == "__license__":
                    if not isinstance(stmt.value, ast.Str):
                        raise ParseError("Value of `__license__` must be a string",stmt.lineno, stmt.col_offset)
                    self.module_license = stmt.value.s

        if not self.type == "Class":
            for target in stmt.targets:
                if isinstance(target, ast.Name):
                    self.declare_variable(target.id)
                elif isinstance(target, ast.Tuple):
                    for elt in target.elts:
                        if isinstance(elt, ast.Name):
                            self.declare_variable(elt.id)

        self.visit(stmt.value)

    def visit_TryFinally(self, node):
        for stmt in node.body:
            self.visit(stmt)
        for stmt in node.finalbody:
            self.visit(stmt)

    def generic_visit(self, node):
        pass

    def visit_Return(self, node):
        self.visit(node.value)

    def visit_For(self, f):
        if isinstance(f.target, ast.Name):
            self.declare_variable(f.target.id)
        else:
            for elt in f.target.elts:
                self.declare_variable(elt.id)
        self.visit_body(f)

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
        if name in self.variables:
            return False
        if self.parent is not None:
            return self.parent.is_variable_free(name)
        return True

    def declare_variable(self, name):
        """
        Returns False if the variable is already declared and True if not.

        """
        if (not name in self.params) and (not name in self.globar_variables) and (not name in self.variables):
            self.variables.append(name)

    def generate_variable(self, base_name):
        name = None
        while True:
            id = self.get_generator_id(base_name)
            if id == 0:
                name = base_name
            else:
                name = "%s%d" % (base_name, id)
            if self.is_variable_free(name):
                self.declare_variable(name)
                break
        return name

    def get_generator_id(self, base_name):
        if base_name not in self.generators:
            self.generators[base_name] = 0
        i = self.generators[base_name]
        self.generators[base_name] = i + 1
        return i

    def __get_docstring(self):
        if len(self.node.body) > 0:
            stmt = self.node.body[0]
            if isinstance(stmt, ast.Expr):
                if isinstance(stmt.value, ast.Str):
                    self.docstring = stmt.value.s

