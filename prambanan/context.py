import ast
from scope import Scope
from prambanan import ParseError


class Context(ast.NodeVisitor):
    """
    First-pass context parser. Builds an execution context for type inference
    and captures docstrings.

    """

    def __init__(self, namespace, node):
        """
        Parse the node as a new context. The parent must be another context
        object. Only Module, Class, Method and Function nodes are allowed.

        """
        self.node = node
        self.stack = []
        self.scope = None

        self.current_scope = None
        self.push_scope("Module", "(Module)")
        self.root_scope = self.current_scope

        self.namespace = namespace

        self.visit_If = self.visit_body
        self.visit_ExceptHandler = self.visit_body

        self.visit(node)


    def push_scope(self, type, name):
        self.stack.append(self.current_scope)
        scope = Scope(type, name, self.current_scope)

        if self.current_scope is not None:
            self.current_scope.identifiers[name] = scope

        self.current_scope = scope

    def pop_scope(self):
        self.current_scope = self.stack.pop()

    def visit_func_or_class(self, node):
        if isinstance(node, ast.ListComp):
            node.name = self.current_scope.generate_list_comp_id()

        if self.current_scope.identifiers.has_key(node.name):
            old_ctx = self.current_scope.identifiers[node.name]
            raise ParseError("%s identifier '%s' at line %d is illegaly overwritten" % (
                old_ctx.type,
                node.name,
                node.lineno),
                node.lineno,
                node.col_offset
                )

        if node.__class__.__name__ == "FunctionDef":
            is_parent_class = self.current_scope.type == "Class"
            self.push_scope("Method" if self.current_scope.type == "Class" else "Function", node.name)
            first = True
            for arg in node.args.args:
                if not (first and is_parent_class):
                    self.current_scope.params.append(arg.id)
                if first:
                    first=False
        elif node.__class__.__name__ == "ClassDef":
            self.push_scope("Class", node.name)
        elif node.__class__.__name__ == "ListComp":
            self.push_scope("ListComp", node.name)

        if self.current_scope.type != "ListComp":
            self.visit_body(node)
            self.__get_docstring(node)

        self.pop_scope()

    def visit_ClassDef(self, c):
        self.current_scope.declare_variable(c.name)
        bases = filter(lambda b: not isinstance(b, ast.Name) or b.id != "object", c.bases)
        if len(bases) == 0:
            self.current_scope.use_builtin("object")
        self.visit_func_or_class(c)

    def visit_FunctionDef(self, c):
        self.current_scope.declare_variable(c.name)
        self.visit_func_or_class( c)

    def visit_Module(self, m):
        m.name = "Module"
        self.visit_func_or_class( m)

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
                self.current_scope.declare_variable(f.target.id)
            elif isinstance(f, ast.Tuple):
                for elt in f.target.elts:
                    self.current_scope.declare_variable(elt.id)
        self.visit_func_or_class(lc)

    def visit_ImportFrom(self, i):
        """
        from module import itema, itemb ->
            module1 = __import__('module'); itema = module1.itema; itemb = module.itemb;
        """
        self.current_scope.use_builtin("__import__")
        module = i.module
        if i.level == 1:
            if module is None:
                module = self.namespace
            else:
                module = self.namespace+"."+module
        for name in i.names:
            varname = name.asname if name.asname else name.name
            self.current_scope.declare_variable(varname)
            self.current_scope.imports[varname] = (module, name.name)

    def visit_Import(self, i):
        """
        import module -> module = __import__(module)
        import namespace.module -> namespace = __import__(namespace)
        import namespace.module as alias -> alias = __import__(namespace.module)
        """
        first = True
        self.current_scope.use_builtin("__import__")
        for name in i.names:
            importname = name.name
            varname = name.name
            if name.asname:
                varname = name.asname
            else:
                if "." in importname:
                    importname = importname[0:importname.find(".")]
                    varname = importname
            self.current_scope.declare_variable(varname)
            self.current_scope.imports[importname] =  (importname, None)

    def visit_Print(self, p):
        """
        Translate print "aa" to print("aa")

        """

        self.current_scope.use_builtin("print")

    def visit_Call(self, node):
        for arg in node.args:
            self.visit(arg)

    def visit_TryExcept(self, node):
        self.visit_body(node)
        for handler in  node.handlers:
            if(handler.name is not None):
                self.current_scope.declare_variable(handler.name.id)
            self.visit_body(handler)

    def visit_Global(self, g):
        for name in g.names:
            self.current_scope.global_variables.append(g)

    def visit_While(self, w):
        self.visit_body(w)

    def visit_Expr(self, expr):
        self.visit(expr.value)

    def visit_body(self, node):
        for stmt in node.body:
            self.visit(stmt)
        for stmt in getattr(node, "orelse", []):
            self.visit(stmt)

    def visit_Assign(self, stmt):
        if self.current_scope.type == "Module":
            if len(stmt.targets) == 1 and isinstance(stmt.targets[0], ast.Name):
                if stmt.targets[0].id == "__all__":
                    if not isinstance(stmt.value, ast.List):
                        raise ParseError("Value of `__all__` must be a list expression",stmt.lineno, stmt.col_offset)
                    self.current_scope.module_all = []
                    for expr in stmt.value.elts:
                        if not isinstance(expr, ast.Str):
                            raise ParseError("All elements of `__all__` must be strings", expr.lineno, expr.col_offset)
                        self.current_scope.module_all.append(expr.s)
                elif stmt.targets[0].id == "__license__":
                    if not isinstance(stmt.value, ast.Str):
                        raise ParseError("Value of `__license__` must be a string",stmt.lineno, stmt.col_offset)
                    self.current_scope.module_license = stmt.value.s

        if not self.current_scope.type == "Class":
            for target in stmt.targets:
                if isinstance(target, ast.Name):
                    self.current_scope.declare_variable(target.id)
                elif isinstance(target, ast.Tuple):
                    for elt in target.elts:
                        if isinstance(elt, ast.Name):
                            self.current_scope.declare_variable(elt.id)

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
            self.current_scope.declare_variable(f.target.id)
        else:
            for elt in f.target.elts:
                self.current_scope.declare_variable(elt.id)
        self.visit_body(f)

    def __get_docstring(self, node):
        if len(node.body) > 0:
            stmt = node.body[0]
            if isinstance(stmt, ast.Expr):
                if isinstance(stmt.value, ast.Str):
                    self.current_scope.docstring = stmt.value.s

