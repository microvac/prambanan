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

    def __init__(self, node, buffer_names, parent = None):
        """
        Parse the node as a new context. The parent must be another context
        object. Only Module, Class, Method and Function nodes are allowed.

        """
        self.docstring = ""
        self.module_license = ""
        self.module_all = None
        self.node = node
        self.generators = {}
        if node.__class__.__name__ == "FunctionDef":
            if parent.type == "Class":
                self.type = "Method"
            else:
                self.type = "Function"
            self.name = node.name
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
        self.list_comp_id = 0

        self.visit_For = self.visit_body
        self.visit_While = self.visit_body
        self.visit_If = self.visit_body
        self.visit_TryExcept = self.visit_body
        self.visit_ExceptHandler = self.visit_body

        self.visit_ClassDef = self.visit_func_or_class
        self.visit_FunctionDef = self.visit_func_or_class
        self.visit_ListComp = self.visit_func_or_class

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
            raise ParseError("%s identifier '%s' at line %d is illegaly overwritten on line %d" % (
                old_ctx.type,
                node.name,
                old_ctx.node.lineno,
                node.lineno,
                ))
        self.identifiers[node.name] = Context(node, self.__buffer_names , self)

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
                        raise ParseError("Value of `__all__` must be a list expression (line %d)" % (stmt.lineno))
                    self.module_all = []
                    for expr in stmt.value.elts:
                        if not isinstance(expr, ast.Str):
                            raise ParseError("All elements of `__all__` must be strings (line %d)" % (expr.lineno))
                        self.module_all.append(expr.s)
                elif stmt.targets[0].id == "__license__":
                    if not isinstance(stmt.value, ast.Str):
                        raise ParseError("Value of `__license__` must be a string (line %d)" % (stmt.lineno))
                    self.module_license = stmt.value.s
        if isinstance(stmt.value, ast.ListComp):
            self.visit(stmt.value)

    def visit_TryFinally(self, node):
        for stmt in node.body:
            self.visit(stmt)
        for stmt in node.finalbody:
            self.visit(stmt)

    def generic_visit(self, node):
        pass

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

    def declare_variable(self, name):
        """
        Returns False if the variable is already declared and True if not.

        """
        if name in self.variables:
            return False
        else:
            self.variables.append(name)
            return True

    def generate_variable(self, base_name):
        id = self.get_generator_id(base_name)
        if id == 0:
            name = base_name
        else:
            name = "%s%d" % (base_name, id)
        self.declare_variable(name)
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

