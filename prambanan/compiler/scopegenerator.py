from logilab.astng.bases import Instance
from logilab.astng.utils import ASTWalker
from logilab.astng import nodes
from prambanan.compiler.utils import ParseError
from .annotation import parse
from scope import Scope

import sys

class ScopeGenerator(ASTWalker):
    """
    First-pass ast visitor. Builds a scope that registers variable, helper for type inference
    and captures docstrings.

    """

    def __init__(self, modname, node):
        ASTWalker.__init__(self, self)
        self.node = node
        self.stack = []
        self.scope = None

        self.current_scope = None
        self.root_scope = None


        self.modname = modname

        self.visit_if = self.visit_body
        self.visit_excepthandler = self.visit_body

    def warn(self, s):
        sys.stderr.write("WARN %s\n" % s)


    def push_scope(self, type, name):
        qname_prefix = "%s." % self.modname if self.modname is not None else ""
        qname = "%s%s" % (qname_prefix, name)

        self.stack.append(self.current_scope)
        scope = Scope(type, qname, name, self.current_scope)

        if self.current_scope is not None:
            self.current_scope.identifiers[name] = scope

        self.current_scope = scope

    def pop_scope(self):
        self.current_scope = self.stack.pop()

    def visit_func_or_class(self, node):

        if self.current_scope is not None and self.current_scope.identifiers.has_key(node.name):
            old_ctx = self.current_scope.identifiers[node.name]
            raise ParseError("%s identifier '%s' at line %d is illegaly overwritten" % (
                old_ctx.type,
                node.name,
                node.lineno),
                node.lineno,
                node.col_offset
                )


        if node.__class__.__name__ == "Function":
            is_parent_class = self.current_scope.type == "Class"
            self.push_scope("Method" if self.current_scope.type == "Class" else "Function", node.name)
            first = True
            for arg in node.args.args:
                if not (first and is_parent_class):
                    self.current_scope.undeclared_variables.append(arg.name)
                if first:
                    first=False
        elif node.__class__.__name__ == "Class":
            self.push_scope("Class", node.name)
        elif node.__class__.__name__ == "ListComp":
            self.push_scope("ListComp", node.name)
        elif node.__class__.__name__ == "Module":
            self.push_scope("Module", node.name)
            self.root_scope = self.current_scope


        if self.current_scope.type != "ListComp":
            self.visit_body(node)
            self.__get_docstring(node)

        self.pop_scope()

    def visit_class(self, c):
        if c.doc is not None:
            annotations = parse(c, self)
            if len(annotations["type"]) > 0:
                if (not hasattr(c, "attr_types")):
                    c.args.arg_types = {}
                c.attr_types.update(annotations["type"])


        self.current_scope.declare_variable(c.name)
        bases = filter(lambda b: not isinstance(b, nodes.Name) or b.name != "object", c.bases)
        if len(bases) == 0:
            self.current_scope.use_builtin("object")
        for base in bases:
            if isinstance(base, nodes.Name):
                self.current_scope.check_builtin_usage(base.name)
        self.visit_func_or_class(c)

    def visit_function(self, c):
        if c.doc is not None:
            annotations = parse(c, self)
            if len(annotations["type"]) > 0:
                if (not hasattr(c.args, "arg_types")):
                    c.args.arg_types = {}
                c.args.arg_types.update(annotations["type"])
        self.current_scope.declare_variable(c.name)
        self.visit_func_or_class( c)

    def visit_module(self, m):
        m.name = "Module"
        self.visit_func_or_class( m)

    def visit_listcomp(self, lc):
        for f in lc.generators:
            if isinstance(f, nodes.Name):
                self.current_scope.declare_variable(f.target.name)
            elif isinstance(f, nodes.Tuple):
                for elt in f.target.elts:
                    self.current_scope.declare_variable(elt.name)

        lc.name = self.current_scope.generate_list_comp_id()
        self.visit_func_or_class(lc)

    def visit_from(self, i):
        self.current_scope.use_builtin("__import__")
        module = i.modname
        level = i.level
        while level > 0:
            if module == "":
                module = self.modname
            else:
                module = self.modname+"."+module
            level -= 1
        for name,asname in i.names:
            if name == "*":
                if module in [self.modname+".native", self.modname+"_native"]:
                    continue
            varname = asname if asname else name
            self.current_scope.declare_variable(varname)
            self.current_scope.imports[varname] = (module, name)

    def visit_import(self, i):
        self.current_scope.use_builtin("__import__")
        for name, asname in i.names:
            importname = name
            varname = name
            if asname:
                varname = asname
            else:
                if "." in importname:
                    importname = importname[0:importname.find(".")]
                    varname = importname
            self.current_scope.declare_variable(varname)
            self.current_scope.imports[importname] =  (importname, None)

    def visit_print(self, p):
        self.current_scope.use_builtin("print")

    def visit_callfunc(self, node):
        for arg in node.args:
            self.visit(arg)

    def visit_tryexcept(self, node):
        self.visit_body(node)
        for handler in  node.handlers:
            if(handler.name is not None):
                self.current_scope.declare_variable(handler.name.name)
            self.visit_body(handler)

    def visit_global(self, g):
        for name in g.names:
            self.current_scope.global_variables.append(g)

    def visit_while(self, w):
        self.visit_body(w)

    def visit_expr(self, expr):
        self.visit(expr.value)

    def visit_discard(self, expr):
        self.visit(expr.value)

    def visit_body(self, node):
        for stmt in node.body:
            self.visit(stmt)
        for stmt in getattr(node, "orelse", []):
            self.visit(stmt)

    def visit_assign(self, stmt):
        if self.current_scope.type == "Module":
            if len(stmt.targets) == 1 and isinstance(stmt.targets[0], nodes.Name):
                if stmt.targets[0].name == "__all__":
                    if not isinstance(stmt.value, nodes.List):
                        raise ParseError("Value of `__all__` must be a list expression",stmt.lineno, stmt.col_offset)
                    self.current_scope.module_all = []
                    for expr in stmt.value.elts:
                        if not isinstance(expr, nodes.Str):
                            raise ParseError("All elements of `__all__` must be strings", expr.lineno, expr.col_offset)
                        self.current_scope.module_all.append(expr.s)
                elif stmt.targets[0].name == "__license__":
                    if not isinstance(stmt.value, nodes.Str):
                        raise ParseError("Value of `__license__` must be a string",stmt.lineno, stmt.col_offset)
                    self.current_scope.module_license = stmt.value.s

        for target in stmt.targets:
            if isinstance(target, nodes.AssName):
                self.current_scope.declare_variable(target.name)
            elif isinstance(target, nodes.Tuple):
                for elt in target.elts:
                    if isinstance(elt, nodes.AssName):
                        self.current_scope.declare_variable(elt.name)

        self.visit(stmt.value)

    def visit_tryfinally(self, node):
        for stmt in node.body:
            self.visit(stmt)
        for stmt in node.finalbody:
            self.visit(stmt)

    def visit_default(self, node):
        pass

    def visit_return(self, node):
        self.visit(node.value)

    def visit_for(self, f):
        if isinstance(f.target, nodes.AssName):
            self.current_scope.declare_variable(f.target.name)
        else:
            for elt in f.target.elts:
                self.current_scope.declare_variable(elt.name)
        self.visit_body(f)

    def __get_docstring(self, node):
        """
        if len(node.body) < 0:
            stmt = node.body[0]
            if isinstance(stmt, ast.Expr):
                if isinstance(stmt.value, ast.Str):
                    self.current_scope.docstring = stmt.value.s
        """

