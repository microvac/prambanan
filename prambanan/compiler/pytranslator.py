#!/usr/bin/env python

#
# PyCow - Python to JavaScript with MooTools translator
# Copyright 2009 Patrick Schneider <patrick.p2k.schneider@gmail.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licki\;enses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

#
# Some Notes:
#
# PyCow does a limited type inference, so it can distinguish function calls
# from class instantiations. However, some conditions can prevent a correct
# evaluation.
#
# PyCow cannot parse comments but can parse docstrings.
#
# No kwargs.
#
from logilab.astng import nodes as ast, builder, scoped_nodes
from logilab.astng.exceptions import UnresolvableName
from logilab.astng.utils import ASTWalker

import simplejson, re, random
from StringIO import StringIO
import inspect
import sys

from .pyscopegenerator import PyScopeGenerator
from .scope import Scope
from . import ParseError, Writer

__all__ = ["translate_file", "translate_string"]

class Translator(ASTWalker):
    """
    Second-pass main parser.

    generated variable names:
        Prambanan.in, Prambanan.subscript, Prambanan.undescore -> same
        module in import from -> _m_
        builtins -> same name
        iterator -> _i, _source, _len, etc
        ex -> _ex


"""
    OP_MAP = {
        "+":	("+", 6, True), # chars, precedence, associates
        "-":	("-", 6, True),
        "*":	("*", 5, True),
        "/":	("/", 5, True),
        #floor div"/":	("/", 5, True),
        "%":	("%", 5, True),
        "**":	("", 5, True),
        #"Pow":	?,
        "<<":	("<<", 7, True),
        ">>":	(">>", 7, True),
        "|":	("|", 12, True),
        "^":	("^", 11, True),
        "&":	("&", 10, True),

        #"uSub":	("-", 4, False),
        #"UAdd": ("+", 4, False),

        "and":	("&&", 13, True),
        "or":	("||", 14, True),

        "not":	("!", 4, False),
        "is not":	("!=", 4, False),

        "==":	("===", 9, True),
        "is":	("===", 9, True),
        "!=":("!==", 9, True),
        "<":	("<", 8, True),
        "<=":	("<=", 8, True),
        ">":	(">", 8, True),
        ">=":	(">=", 8, True),
        }

    NO_SEMICOLON = [
        "Global",
        "If",
        "While",
        "For",
        "TryExcept",
        "TryFinally",
        "Pass",
        ]

    RESERVED_WORDS = [
        "null",
        "undefined",
        "true",
        "false",
        "new",
        "var",
        "switch",
        "case",
        "function",
        "this",
        "default",
        "throw",
        "delete",
        "instanceof",
        "typeof",
        ]


    IDENTIFIER_RE = re.compile("^[A-Za-z_$][0-9A-Za-z_$]*$")

    HEADER_BUFFER = "header"
    BODY_BUFFER = "body"
    FOOTER_BUFFER = "footer"

    BUFFER_NAMES = [HEADER_BUFFER, BODY_BUFFER, FOOTER_BUFFER]

    LIB_NAME = "prambanan"

    def __init__(self, scope, config):
        ASTWalker.__init__(self, self)
        self.mod_scope = scope
        self.curr_scope = None

        self.writer_stack = []

        self.input_name = config["input_name"]
        self.input_lines = config["input_lines"]
        self.out = config["output"]
        self.namespace = config["namespace"]
        self.__warnings = config["warnings"]
        self.bare = config["bare"]

        self.use_throw_helper = "use_throw_helper" in config
        if "overridden_types" in config:
            self.overridden_types = config["overridden_types"]
        else:
            self.overridden_types = {}

        self.export_map = {}
        self.public_identifiers = []
        self.translated_names = {}
        self.util_names = {}

        class Executor(object):
            def __init__(cur):
                cur.result = ""
            def __enter__(cur):
                self.writer_stack.append(self.curr_writer)
                self.curr_writer = Writer(self.BODY_BUFFER, self.BUFFER_NAMES)
                return cur
            def __exit__(cur, *args):
                header = "".join(self.curr_writer.buffers[self.HEADER_BUFFER])
                body = "".join(self.curr_writer.buffers[self.BODY_BUFFER])
                cur.result = header+body
                self.curr_writer = self.writer_stack.pop()
        self.Executor = Executor

    def visit_module(self, mod):
        """
        Initial node.
        There is and can be only one Module node.

        """
        self.curr_writer = Writer(self.BODY_BUFFER, self.BUFFER_NAMES)
        self.curr_scope = self.mod_scope

        if not self.bare:
            self.__change_buffer(self.HEADER_BUFFER)
            if mod.doc:
                self.__write_docstring(self.mod_scope.docstring)

            self.__write("(function(%s) {" % self.LIB_NAME)
            self.__change_buffer(self.BODY_BUFFER)

            public_identifiers = self.mod_scope.module_all
            not_all_exists = public_identifiers is None
            if not_all_exists:
                public_identifiers = []

        for k, v in self.export_map.items():
            self.mod_scope.declare_variable(k)
            self.__write("%s = %s.%s;" % (k, self.LIB_NAME, v))

        for stmt in mod.body:
            if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 and\
               isinstance(stmt.targets[0], ast.Name) and\
               stmt.targets[0].name in ("__all__", "__license__"):
                continue
            """
            if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Str):
                continue # Module docstring
            """

            if not self.bare and not_all_exists:
                for name in self.__get_identifiers(stmt):
                    if name is not None and not name.startswith("_"):
                        public_identifiers.append(name)

            self.visit(stmt)
            if( not isinstance(stmt, ast.Import) and not isinstance(stmt, ast.From) and not isinstance(stmt, ast.Pass)):
                self.__semicolon(stmt)

        if not self.bare:
            self.public_identifiers.extend(public_identifiers)

            get_name = lambda name: name if name not in self.translated_names else self.translated_names[name]
            exported = (self.exe_first_differs(sorted(set(self.public_identifiers)), rest_text=",",
                do_visit=lambda name: self.__write("%s: %s" % (name, get_name(name)))))

            self.__write("%s.exports('%s',{%s});})(%s);" % (self.LIB_NAME, self.namespace, exported, self.LIB_NAME))

        builtin_var = None
        builtins = set(self.mod_scope.all_used_builtins())
        if len(builtins) > 0:
            builtin_var = self.curr_scope.generate_variable("__builtin__")
            for builtin in builtins:
                self.curr_scope.declare_variable(builtin)

        self.__change_buffer(self.HEADER_BUFFER)
        self.__write_variables()

        if len(builtins) > 0:
            self.__write("%s = %s.import('__builtin__');" %(builtin_var, self.LIB_NAME))
            for builtin in builtins:
                self.__write("%s = %s.%s;" %(builtin, builtin_var, builtin))

        for item in self.util_names.values():
            name, value = item
            self.__write("%s = %s;" %(name, value))

        self.out.write("".join(self.curr_writer.buffers[self.HEADER_BUFFER]))
        self.out.write("".join(self.curr_writer.buffers[self.BODY_BUFFER]))
        self.curr_scope = None


    def visit_from(self, i):
        """
        from module import itema, itemb ->
            module1 = __import__('module'); itema = module1.itema; itemb = module.itemb;
        """
        module = i.modname
        if i.level == 1:
            if module is None:
                module = self.namespace
            else:
                module = self.namespace+"."+module
        modulevarname = module if "." not in module else module[0:module.find(".")]
        modulevarname = self.curr_scope.generate_variable("_m_"+modulevarname)
        self.__write("%s = __import__('%s'); " % (modulevarname, module))
        for name,asname in i.names:
            varname = asname if asname else name
            self.__write("%s = %s.%s;  " % (varname, modulevarname, name))

    def visit_import(self, i):
        """
        import module -> module = __import__(module)
        import namespace.module -> namespace = __import__(namespace)
        import namespace.module as alias -> alias = __import__(namespace.module)
        """
        first = True
        for name, asname in i.names:
            importname = name
            varname = name
            if asname:
                varname = asname
            else:
                if "." in importname:
                    importname = importname[0:importname.find(".")]
                    varname = importname
            self.__write("%s = __import__('%s');" % (varname, importname))

    def infer_call_type(self, func):
        cls = self.curr_scope.class_context()
        if isinstance(func, ast.Name):
            if self.curr_scope.check_builtin_usage(func.name):
                if func.name in Scope.BUILTINS_FUNC:
                    return "Function"
                else:
                    return "Class"
        elif isinstance(func, ast.Getattr):
            if cls is not None and isinstance(func.expr, ast.CallFunc) and isinstance(func.expr.func, ast.Name) :
                if func.expr.func.name == "super":
                    return "Function"

        is_class = False
        is_func = False
        try:
            for inferred in func.infer():
                qname = inferred.qname()
                if qname in self.overridden_types:
                    return self.overridden_types[qname]
                if isinstance(inferred, ast.Class):
                    is_class = True
                elif isinstance(inferred, ast.Function):
                    is_func = True
        except UnresolvableName, InferenceError:
            return None

        if is_class and is_func:
            return None
        if is_class:
            return "Class"
        if is_func:
            return "Function"
        return None

    def visit_callfunc(self, c):
        """
        Translates a function/method call or class instantiation.
        every named arguments became keyword arguments
        """

        cls = self.curr_scope.class_context()

        type = self.infer_call_type(c.func)
        name = None
        call_type = None
        method_written = False
        if isinstance(c.func, ast.Name):
            call_type = "name"
            if c.func.name == "JS":
                if len(c.args) != 1:
                    raise ParseError("native js only accept one argument", c.lineno, c.col_offset)
                if not isinstance(c.args[0], ast.Const) and not isinstance(c.args[0].value, str):
                    raise ParseError("native js only accept string",c.lineno, c.col_offset)
                self.__write(re.sub(r'(?:@{{[!]?)([^}}]*)(?:}})', r"\1",c.args[0].value))
                return
        elif isinstance(c.func, ast.Getattr):
            call_type = "getattr"
            if cls is not None and isinstance(c.func.expr, ast.CallFunc) and isinstance(c.func.expr.func, ast.Name) :
                if c.func.expr.func.name == "super":
                    # A super call
                    if (not len(c.func.expr.args) == 2):
                        self.raise_error("Only python 2 simple super supported", c)
                    attrname = c.func.attrname
                    self.__write("%s(" % self.get_util_var_name("_super", "%s.helpers.super" % self.LIB_NAME))
                    self.__write("this, '%s')" %  attrname)
                    method_written = True

        if type is None and "type" in self.__warnings:
            sys.stderr.write(" Warning: Cannot infer type [ call: %s, name: %s ] in line %s\n" % (call_type, name, c.lineno ))
        elif type == "Class":
            self.__write("new ")

        if not method_written:
            self.visit(c.func)
        self.__write("(")
        self.__parse_call_args(c)
        self.__write(")")

    def visit_assname(self, n):
        if n.name in self.RESERVED_WORDS:
            if not n.name in self.translated_names:
                self.translated_names[n.name] = self.mod_scope.generate_variable("__keyword_"+n.name)
            self.__write(self.translated_names[n.name])
        else:
            self.__write(n.name)

    def visit_delname(self, n):
        pass

    def visit_name(self, n):
        """
        Translate an identifier. If the context is a method, substitute `self`
        with `this`.

        Some special keywords:
        True -> true
        False -> false
        None -> null

        """
        self.curr_scope.check_builtin_usage(n.name)
        self.visit_assname(n)

    def visit_binop(self, o):
        """
        Translates a binary operator.
        Note: The modulo operator on strings is translated to left.sprintf(right)
        and currently the only spot where tuples are allowed.

        """
        if o.op == "%" and not (isinstance(o.left, ast.Const) and isinstance(o.left.value, int)):
            args = self.exe_first_differs(o.right.elts, rest_text=",") if isinstance(o.right, ast.Tuple) else self.exe_node(o.right)
            self.__write("%s.__mod__(%s)" % (self.exe_node(o.left), args))
        elif o.op == "**":
            pow_helper = self.get_util_var_name("_pow", "%s.helpers.pow" % self.LIB_NAME)
            self.__write("%s(%s, %s)" % (pow_helper, self.exe_node(o.left), self.exe_node(o.right)))
        else:
            chars, prec, assoc = self.__get_op_cpa(o.op)
            self.visit(o.left)
            self.__write(" %s " % (chars))
            eprec, eassoc = self.__get_expr_pa(o.right)
            if eprec >= prec: self.__write("(")
            self.visit(o.right)
            if eprec >= prec: self.__write(")")

    def visit_boolop(self, o):
        """
        Translates a boolean operator.

        """
        first = True
        chars, prec, assoc = self.__get_op_cpa(o.op)
        for expr in o.values:
            if first:
                first = False
            else:
                self.__write(" %s " % (self.__get_op(o.op)))
            eprec, eassoc = self.__get_expr_pa(expr)
            if eprec >= prec: self.__write("(")
            self.visit(expr)
            if eprec >= prec: self.__write(")")

    def visit_unaryop(self, o):
        """
        Translates a unary operator.

        """
        self.__write(self.__get_op(o.op))
        prec, assoc = self.__get_expr_pa(o.operand)
        if isinstance(o.operand, ast.Const): prec = 3
        if prec > 2: self.__write("(")
        self.visit(o.operand)
        if prec > 2: self.__write(")")

    def visit_compare(self, c):
        """
        Translate a compare block.

        """
        inits = []
        remaining = [len(c.ops)]
        left_text = [self.exe_node(c.left)]
        def op_executor(ops):
            op, expr = ops
            if len(c.ops) > 1:
                self.__write("(")

            if remaining[0] > 1:
                if not isinstance(expr, ast.Const) and not isinstance(expr, ast.Name):
                    right_text = self.curr_scope.generate_variable("_op")
                    inits.append("%s = %s;"% (right_text, self.exe_node(expr)))
                else:
                    right_text = self.exe_node(expr)
            else:
                right_text = self.exe_node(expr)

            if op != "in" and op != "not in":
                self.__write(left_text[0])

            if op == "in" or op == "not in":
                if op == "not in":
                    self.__write(" !")
                in_helper = self.get_util_var_name("_in", "%s.helpers.in"%self.LIB_NAME)
                self.__write(" %s(%s, %s) " % (in_helper, left_text[0], right_text))
            else:
                self.__write(" %s " % (self.__get_op(op)))
                prec, assoc = self.__get_expr_pa(expr)
                if prec > 2: self.__write("(")
                self.__write(right_text)
                if prec > 2: self.__write(")")
            left_text[0] = right_text
            remaining[0] = remaining[0] - 1
            if len(c.ops) > 1:
                self.__write(")")

        body = self.exe_first_differs(c.ops, rest_text="&&", do_visit=op_executor)
        c.inits = inits
        self.__write(body)

    def visit_dict(self, d):
        """
        Translate a dictionary expression.

        """
        with self.Executor() as items:
            first = True
            for key, value in d.items:
                if first:
                    first = False
                else:
                    self.__write(",")
                if not isinstance(key, ast.Const):
                    self.raise_error("Only numbers and string literals are allowed in dictionary expressions", key)
                if isinstance(key.value, int):
                    self.__write("%d: " % (key.value))
                else:
                    if self.IDENTIFIER_RE.match(key.value):
                        self.__write("%s: " % (key.value))
                    else:
                        self.__write("\"%s\": " % (key.value))
                self.visit(value)
        self.__write("{%s}" % items.result)

    def visit_subscript(self, s):
        """
        Translate a subscript expression.

        """

        #   optimize simple index slice
        if isinstance(s.parent, ast.Assign) or isinstance(s.parent, ast.Discard):# or isinstance(s.parent, ast.Load) or isinstance(s.parent, ast.Store) :
            if isinstance(s.slice, ast.Index) and isinstance(s.slice.value, ast.Const) and s.slice.value.value >= 0:
                s.simple = True
                self.__write('%s[%s]' % (self.exe_node(s.value), self.exe_node(s.slice.value)))
                return
            if isinstance(s.slice, ast.Index) and isinstance(s.slice.value, ast.Const) and isinstance(s.slice.value.value, str) :
                s.simple = True
                self.__write('%s[%s]' % (self.exe_node(s.value), self.exe_node(s.slice.value)))
                return

        func = ""
        s.simple = True
        if isinstance(s.parent, ast.Delete):
            func = "d"
        elif isinstance(s.parent, ast.Assign) and s in s.parent.targets:
            func = "s"
            s.simple = False
        else:
            func = "l"

        subscript = self.get_util_var_name("_subscript", ("%s.helpers.subscript" % self.LIB_NAME))
        value = self.exe_node(s.value)
        with self.Executor() as args:
            if isinstance(s.slice, ast.Index):
                type='i'
                self.__write("%s" % ("null" if s.slice.value is None else self.exe_node(s.slice.value)))
            elif isinstance(s.slice, ast.Slice):
                type="s"
                self.__write("%s" % ("null" if s.slice.lower is None else self.exe_node(s.slice.lower)))
                self.__write(", %s" % ("null" if s.slice.upper is None else self.exe_node(s.slice.upper)))
                self.__write(", %s" % ("null" if s.slice.step is None else self.exe_node(s.slice.step)))
            else:
                self.raise_error("Subscript slice type '%s' is not supported" % (str(s.slice.__class__.__name__)), s)

        self.__write("%s.%s.%s(%s,%s" % (subscript, func, type, value, args.result))

        if s.simple:
            self.__write(")")

    def visit_assign(self, a):
        """
        Translate an assignment.
        if target is tuple, became self executable function:
            (a, b) = c
        if value is tuple make array:
            c = (a, b)
                => c = [a, b]

        """
        is_target_tuple = False
        tuple_target = None
        for target in a.targets:
            if isinstance(target, ast.Tuple):
                is_target_tuple = True
                tuple_target = target

        if is_target_tuple and len(a.targets) > 1:
            self.raise_error("tuple are not allowed on multiple assignment", tuple_target)

        if is_target_tuple:
            self.__write("(function(_source){")
            tuple = a.targets[0]
            for i in range(0, len(target.elts)):
                elt = tuple.elts[i]
                self.visit(elt)
                self.__write(" = _source[%d]; " % i)
            self.__write("})(")
        else:
            for target in a.targets:
                self.visit(target)
                if isinstance(target, ast.Subscript) and not target.simple:
                    self.__write(", ")
                else:
                    self.__write(" = ")

        if isinstance(a.value, ast.Tuple):
            self.__write("[%s]" % self.exe_first_differs(a.value.elts, rest_text=","))
        else:
            self.visit(a.value)

        if is_target_tuple:
            self.__write(")")
        if isinstance(target, ast.Subscript) and not target.simple:
            self.__write(")")

    def visit_augassign(self, a):
        """
        Translate an assignment operator.

        """
        self.visit(a.target)
        if isinstance(a.value, ast.Const) and a.value == 1:
            if isinstance(a.op, ast.Add):
                self.__write("++")
                return
            elif isinstance(a.op, ast.Sub):
                self.__write("--")
                return
        self.__write(" %s= " % (self.__get_op(a.op[:-1])))
        self.visit(a.value)

    def visit_for(self, f):
        """
        Translate a for loop.

        """
        i_var = self.curr_scope.generate_variable("_i")
        len_var = self.curr_scope.generate_variable("_len")
        is_tuple = False

        if isinstance(f.target, ast.AssName):
            iter_var = f.target.name
        else:
            is_tuple = True
            iter_var = []
            for elt in f.target.elts:
                t = elt.name
                iter_var.append(t)

        list_var = self.curr_scope.generate_variable("_list")
        init = ""

        if not is_tuple:
            init = ("%s = %s[%s];" % (iter_var, list_var, i_var))
        else:
            for i in range(0, len(iter_var)):
                init = init + ("%s = %s[%s][%d];" % (iter_var[i], list_var, i_var, i))

        self.__write("%s = %s;" % (list_var, self.exe_node(f.iter)))
        self.__write("for (%s = 0, %s = %s.length; %s < %s; %s++) {" % (i_var, len_var, list_var, i_var, len_var, i_var))
        self.__write("   %s" % init)
        self.__write("   %s" % self.exe_body(f.body))
        self.__write("}")
        if len(f.orelse) > 0:
            self.__write("if(%s == %s){%s}" % (i_var, len_var, self.exe_body(f.orelse)))


    def visit_class(self, c):
        """
        Translates a Python class into Javascript class
        This inserts a Class context which influences the translation of
        functions and assignments.

        """
        fullname = "t__%s_" % c.name if self.namespace == "" else "t_%s_%s" % (self.namespace.replace(".", "_"), c.name)
        ctor_name = self.curr_scope.generate_variable("%s" % fullname, declared=False)
        self.__push_context(c.name)

        bases = filter(lambda b: not isinstance(b, ast.Name) or b.name != "object", c.bases)
        if len(bases) > 0:
            bases_param = "[%s]" % self.exe_first_differs(bases, rest_text=", ")
        else:
            bases_param = "[object]"

        self.__change_buffer(self.HEADER_BUFFER)


        # Named constructor function
        self.__write("function %s(){ this.__init__.apply(this, arguments); } " % (ctor_name))
        if c.doc:
            self.__write_docstring(c.doc)
        create_class = self.get_util_var_name("_class", "%s.helpers.class" %self.LIB_NAME)
        self.__write("%s = %s(%s, %s, function(){" % (c.name, create_class, ctor_name, bases_param))


        self.__change_buffer(self.BODY_BUFFER)

        exported = []
        proto_only = []
        cls_only = []
        # Instance member
        for stmt in c.body:
            exported.extend(self.__get_identifiers(stmt))
            if isinstance(stmt, ast.Function):
                decorators = self.__get_special_decorators(stmt)
                if not "staticmethod" in decorators:
                    proto_only.append(stmt.name)
                else:
                    cls_only.append(stmt.name)

            self.visit(stmt)
            self.__semicolon(stmt);

        all_attrs = set(exported).difference(set(proto_only)).difference(set(cls_only))

        def write_attrs(attrs):
            content = self.exe_first_differs(attrs, rest_text = ",", do_visit = lambda(x): self.__write("%s:%s" %(x, x)))
            self.__write("{%s}"% content)

        content = self.exe_first_differs([proto_only, cls_only, all_attrs], rest_text = ",", do_visit = lambda(x): write_attrs(x))
        self.__write("return [%s]" % content)


        self.__write("})")
        self.__write_decorators(c)

        self.__pop_context()

    def visit_function(self, f):
        """
        Translate a Python function into a JavaScript function.
        Depending on the context, it is translated to `var name = function (...)`
        or `name: function (...)`.

        """
        self.__push_context(f.name)


        is_method = self.curr_scope.type == "Method"

        # Special decorators
        decorators = self.__get_special_decorators(f)
        is_static = decorators.has_key("staticmethod")

        self.__change_buffer(self.HEADER_BUFFER)

        # Write docstring
        if f.doc:
            self.__write_docstring(f.doc)

        # Declaration
        self.__write("%s = function (" % f.name)

        # Parse arguments
        self.__parse_args(f.args, is_method and not is_static)
        self.__write(") {")

        self.__change_buffer(self.BODY_BUFFER)

        # Handle default value, var args, kwargs
        self.__parse_defaults(f.args, is_method and not is_static)


        # Write self = this
        if is_method and not is_static:
            self.curr_scope.declare_variable(f.args.args[0].name)
            self.__write("%s = this;"%f.args.args[0].name)

        # Function body
        if "JSNoOp" in decorators:
            self.__write("return undefined;")
        else:
            self.__write(self.exe_body(f.body, True, True))

        self.__write("}")
        self.__write_decorators(f)

        self.__pop_context()


    def visit_tryexcept(self, tf):
        ex_var = self.curr_scope.generate_variable("_ex")

        self.__write("try{ %s }" % self.exe_body(tf.body, True, True))
        self.__write("catch (%s){" % ex_var)
        has_first = False
        has_catch_all = False
        for handler in tf.handlers:
            has_if = False
            if handler.type is not None:
                if has_first:
                    self.__write("else ")
                if(isinstance(handler.type, ast.Getattr) or isinstance(handler.type, ast.Name)):
                    self.__write("if (%s instanceof %s){" %(ex_var, self.exe_node(handler.type)))
                elif(isinstance(handler.type, ast.Tuple)):
                    self.__write("if (%s){" % self.exe_first_differs(handler.type.elts,
                        rest_text="||",
                        do_visit=lambda elt: self.__write("(%s instanceof %s)" % (ex_var, self.exe_node(elt)))
                    ))
                else:
                    self.raise_error("handler type not recognized %s" % handler.type.__class__.name, handler.type)
                has_if = has_first = True
            else:
                has_catch_all = True
                if has_first:
                    self.__write("else {")
                    has_if = True
                has_first = True
            if handler.name is not None:
                self.__write("%s = %s;" %(handler.name.name, ex_var))
            self.__write(self.exe_body(handler.body, True, True))
            if has_if:
                self.__write("}");
        if not has_catch_all:
            if has_first:
                if self.use_throw_helper:
                    throw = self.get_util_var_name("_throw", "%s.helpers.throw" %self.LIB_NAME)
                    file = self.get_util_var_name("__py_file__", "'%s'" % self.input_name)
                    self.__write("else { %s(%s, %s, %d); }"% (throw, ex_var, file, tf.lineno))
                else:
                    self.__write("else { throw %s }" % ex_var)
        self.__write("}");

    def visit_listcomp(self, lc):
        """
        [expr for item if expr in lists] ->
            (function(){
                var _i, _len, _results;
                _results = []
            })();
        """
        if len(lc.generators) > 1:
            self.raise_error("Could only support one generator now",  lc.generators[1].target)

        f = lc.generators[0]

        is_tuple = False

        if isinstance(f.target, ast.AssName):
            iter_var = f.target.name
        else:
            is_tuple = True
            iter_var = []
            for elt in f.target.elts:
                t = elt.name
                iter_var.append(t)

        self.__push_context(lc.name)
        self.__change_buffer(self.HEADER_BUFFER)
        self.__write(" (function(){ ")
        self.__change_buffer(self.BODY_BUFFER)

        i_var = self.curr_scope.generate_variable("_i")
        len_var = self.curr_scope.generate_variable("_len")
        results_var = self.curr_scope.generate_variable("_results")

        list_var = self.curr_scope.generate_variable("_list")
        iter_name = self.get_util_var_name("_iter", "%s.helpers.iter" %self.LIB_NAME);

        self.__write("%s = []; " % results_var)
        self.__write("%s = %s(%s); " % (list_var, iter_name, self.exe_node(f.iter)))
        self.__write("for (%s = 0, %s = %s.length; %s < %s; %s++) {" % (i_var, len_var, list_var, i_var, len_var, i_var))
        if not is_tuple:
            self.__write(    "%s = %s[%s];" % (iter_var, list_var, i_var))
        else:
            for i in range(0, len(iter_var)):
                self.__write("%s = %s[%s][%d];" % (iter_var[i], list_var, i_var, i))
        for _if in f.ifs:
            self.__write("    if (%s)" % self.exe_node(_if))
        self.__write(            "%s.push(%s);" % (results_var, self.exe_node(lc.elt)))
        self.__write("}")
        self.__write("return %s;" % results_var)
        self.__write("})()")

        self.__pop_context()


    def visit_raise(self, r):
        exc = self.exe_node(r.exc)

        if self.use_throw_helper:
            throw = self.get_util_var_name("_throw", "%s.helpers.throw" %self.LIB_NAME)
            file = self.get_util_var_name("__py_file__", "'%s'" % self.input_name)
            self.__write("%s(%s, %s, %d)"% (throw, exc, file, r.lineno))
        else:
            self.__write("throw %s" % exc)

    def visit_print(self, p):
        """
        Translate print "aa" to print("aa")

        """
        self.__write("print(%s)" % self.exe_first_differs(p.values, rest_text=","))

    def visit_discard(self, v):
        self.visit(v.value)

    def visit_const(self, t):
        if isinstance(t.value, str):
            self.__write(simplejson.dumps(t.value))
        elif isinstance(t.value, bool):
            self.__write(str(t.value).lower())
        elif isinstance(t.value, int) or isinstance(t.value, float):
            self.__write(str(t.value))
        elif t.value is None:
            self.__write("null")
        else:
            raise ValueError("const not recognized")


    def visit_global(self, g):
        """
        Declares variables as global.

        """
        pass

    def visit_lambda(self, l):
        """
        Translates a lambda function.

        """
        with self.Executor() as args:
            self.__parse_args(l.args)
        self.__write("function(%s) {return %s; }" % (args.result, self.exe_node(l.body)))

    def visit_yield(self, y):
        """
        Translate the yield operator.

        """
        self.raise_error("yield are not supported", y)

    def visit_return(self, r):
        """
        Translate the return statement.

        """
        if r.value:
            self.__write("return %s" % self.exe_node(r.value))
        else:
            self.__write("return")

    def visit_list(self, l):
        """
        Translate a list expression.

        """
        self.__write("[%s]" % self.exe_first_differs(l.elts, rest_text=","))

    def visit_delete(self, d):
        """
        Translate a delete statement.

        """
        for target in d.targets:
            if isinstance(target, ast.Subscript):
                self.visit(target)
            else:
                self.__write("delete %s" % self.exe_node(target))


    def visit_pass(self, p):
        """
        Translate the `pass` statement. Places a comment.

        """
        self.__write("/* pass */")

    def visit_continue(self, c):
        """
        Translate the `continue` statement.

        """
        self.__write("continue")

    def visit_break(self, c):
        """
        Translate the `break` statement.

        """
        self.__write("break")

    def visit_getattr(self, a):
        """
        Translate an attribute chain.

        """
        self.__write("%s.%s" % (self.exe_node(a.expr), a.attrname))

    def visit_assattr(self, a):
        """
        Translate an attribute chain.

        """
        self.__write("%s.%s" % (self.exe_node(a.expr), a.attrname))


    def visit_if(self, i):
        """
        Translate an if-block.

        """
        test = self.exe_node(i.test)
        if isinstance(i.test, ast.Compare):
            self.__write("".join(i.test.inits))
        self.__write("if ( %s ) { %s }" % (test, self.exe_body(i.body)))
        if len(i.orelse) > 0:
            self.__write("else {%s}" % self.exe_body(i.orelse))


    def visit_ifexp(self, i):
        """
        Translate an if-expression.

        """
        test = self.exe_node(i.test)
        if isinstance(i.test, ast.Compare):
            if len(i.test.inits) > 0:
                self.raise_error("if else node cannot have complicated multiple comparison", i)
        self.__write("%s ? %s : %s" % (test, self.exe_node(i.body), self.exe_node(i.orelse)))

    def visit_while(self, w):
        """
        Translate a while loop.

        """
        if len(w.orelse) > 0:
            self.raise_error("`else` branches of the `while` statement are not supported", w.orelse[0])

        test = self.exe_node(w.test)
        if isinstance(w.test, ast.Compare):
            self.__write("".join(w.test.inits))

        self.__write("while (%s){ %s }" % (test, self.exe_body(w.body)))



    def visit_tryfinally(self, tf):
        self.__write("try{ %s } finally { %s }" % (self.exe_body(tf.body, True, True),  self.exe_body(tf.finalbody, True, True)))

    def visit_assert(self, a):
        pass

    def visit_tuple(self, t):
        self.__write("[%s]" % self.exe_first_differs(t.elts, rest_text=","))

    def visit_default(self, node):
        raise ParseError("Could not parse node type '%s'" % str(node.__class__.__name__), node.lineno, node.col_offset)

    def __parse_call_args(self, args, comma_first=False):
        """
        Translate a list of arguments.

        """
        first = True
        i = 0
        for arg in args.args:
            if (not first) or comma_first:
                self.__write(", ")
            first = False
            if isinstance(arg, ast.Keyword):
                make_kwargs = self.get_util_var_name("_make_kwargs", "%s.helpers.make_kwargs" % self.LIB_NAME)
                kwargs = self.exe_first_differs(args.args[i:], rest_text=",",do_visit=lambda arg: self.__write("%s:%s" % (arg.arg, (self.exe_node(arg.value)))))
                self.__write("%s({%s})" % (make_kwargs, kwargs))
                break
            else:
                self.visit(arg)
            i += 1

        if args.starargs is not None:
            if (not first) or comma_first:
                self.__write(", ")
            first = False
            self.__write(self.exe_node(args.starargs))

        if args.kwargs is not None:
            if (not first) or comma_first:
                self.__write(", ")
            first = False
            self.__write(self.exe_node(args.kwargs))

            """
        if len(args.keywords) > 0:
            #todo has keywords and kwargs
            if (not first) or comma_first:
                self.__write(", ")
            first = False
            """


    def __parse_args(self, args, strip_first = False):
        """
        Translate a list of arguments.

        """
        first = True
        for arg in args.args:
            if first:
                if strip_first and isinstance(arg, ast.Name):
                    strip_first = False
                    continue
                first = False
            else:
                self.__write(", ")
            self.visit(arg)

        if args.vararg is not None:
            if first:
                first = False
            else:
                self.__write(", ")
            self.__write(args.vararg)

        if args.kwarg is not None:
            if first:
                first = False
            else:
                self.__write(", ")
            self.__write(args.kwarg)

    def __parse_defaults(self, args, strip_first=False):
        """
        Translate the default arguments list.
        """
        if len(args.defaults) > 0 or args.vararg is not None or args.kwarg is not None:
            args_name = self.curr_scope.generate_variable("_args")
            init_args = self.get_util_var_name("_init_args", ("%s.helpers.init_args" % self.LIB_NAME))
            self.__write("%s = %s(arguments);" % (args_name , init_args))

        if len(args.defaults) > 0:
            first = len(args.args) - len(args.defaults)
            for i in xrange(len(args.defaults)):
                get_arg = self.get_util_var_name("_get_arg", ("%s.helpers.get_arg" % self.LIB_NAME))
                arg_name = self.exe_node(args.args[first+i])
                index = first + i;
                if strip_first:
                    index -= 1
                self.__write("%s = %s(%d, \"%s\", %s, %s);" % (arg_name, get_arg, index, arg_name, args_name, self.exe_node(args.defaults[i])))

        if args.vararg is not None:
            get_varargs = self.get_util_var_name("_get_varargs", ("%s.helpers.get_varargs" % self.LIB_NAME))
            index = len(args.args)
            if strip_first:
                index -= 1
            self.__write("%s = %s(%d, %s);" % (args.vararg, get_varargs, index, args_name))

        if args.kwarg is not None:
            get_kwargs = self.get_util_var_name("_get_kwargs", ("%s.helpers.get_kwargs" % self.LIB_NAME))
            self.__write("%s = %s(%s);" % (args.kwarg, get_kwargs, args_name))


    def __get_identifiers(self, stmt):
        names = []
        if isinstance(stmt, ast.Class) or isinstance(stmt, ast.Function):
            names.append(stmt.name)
        if isinstance(stmt, ast.Assign):
            for target in stmt.targets:
                if isinstance(target, ast.Name):
                    names.append(target.name)
        return names


    def __get_special_decorators(self, stmt):
        """
        Return a dictionary of decorators and their parameters.

        """
        decorators = {}
        if isinstance(stmt, ast.Function) and stmt.decorators is not None:
            for dec in stmt.decorators.nodes:
                if isinstance(dec, ast.Name):
                    if dec.name in ["staticmethod", "JSNoOp"] :
                        decorators[dec.name] = []
                        continue
        return decorators

    def __write_decorators(self, stmt):
        current = stmt.name
        if stmt.decorators is None:
            return

        for dec in stmt.decorators.nodes:
            if isinstance(dec, ast.Name):
                if dec.name in ["staticmethod", "JSNoOp"] :
                    continue
                header = "%s" % dec.name
            elif isinstance(dec, ast.CallFunc):
                with self.Executor() as call:
                    self.visit(dec.func)
                    self.__write("(")
                    self.__parse_call_args(dec)
                    self.__write(")")
                header = call.result
            else:
                self.raise_error("This class decorator is not supported. Only decorators of pycow.decorators are supported",dec)
            current = "%s(%s)" % (header, current)

        self.__write(";%s = %s" % (stmt.name, current))


    def __get_op(self, op):
        """
        Translates an operator.

        """
        return self.OP_MAP[op][0]

    def __get_op_cpa(self, op):
        """
        Get operator chars, precedence and associativity.

        """
        return self.OP_MAP[op]

    def __get_expr_pa(self, expr):
        """
        Get the precedence and associativity of an expression.

        """
        name = expr.__class__.__name__
        if name in ("BoolOp", "BinOp", "UnaryOp"):
            return self.__get_op_cpa(expr.op)[1:]
        elif name in ("Lambda", "Dict", "List", "Num", "Str", "Name", "Const"):
            return (1, False)
        elif name == "IfExp":
            return (15, False)
        elif name in ("Getattr", "Subscript"):
            return (1, True)
        elif name in ("CallFunc", "Repr"):
            return (2, True)
        elif name == "Compare":
            return (8, True)

    def __change_buffer(self, buffer_name):
        self.curr_writer.change_buffer(buffer_name)

    def __write(self, s):
        self.curr_writer.write(s)

    def __write_docstring(self, s):
        self.__write("\n/**\n")
        gotnl = False
        first = True
        for line in s.split("\n"):
            line = line.strip()
            if line == "":
                gotnl = True
            else:
                if gotnl and not first:
                    self.__write(" *")
                gotnl = False
                first = False
                self.__write(" * %s\n" % (line))
        self.__write(" */\n")

    def __write_variables(self):
        if len(self.curr_scope.variables) > 0:
            first = True
            for variable in sorted(self.curr_scope.variables):
                if first:
                    self.__write("var ")
                    first = False
                else:
                    self.__write(", ")
                name = self.translated_names.get(variable, variable)
                self.__write(name)
            self.__write(";")



    def __push_context(self, identifier):
        """
        Walk context up.

        """
        old_context = self.curr_scope
        self.curr_scope = self.curr_scope.child(identifier)
        if self.curr_scope is None:
            raise ParseError("Lost context on accessing '%s' from '%s (%s)'" % (identifier, old_context.name, old_context.type))

        self.writer_stack.append(self.curr_writer)
        old_writer = self.curr_writer
        self.curr_writer = Writer(self.BODY_BUFFER, self.BUFFER_NAMES)
        self.curr_writer.indent_level = old_writer.indent_level

    def __pop_context(self):
        """
        Walk context down.

        """
        self.__change_buffer(self.HEADER_BUFFER)

        self.__write_variables()
        self.curr_scope = self.curr_scope.parent

        old_writer = self.writer_stack.pop()
        old_writer.buffers[self.BODY_BUFFER].extend(self.curr_writer.buffers[self.HEADER_BUFFER])
        old_writer.buffers[self.BODY_BUFFER].extend(self.curr_writer.buffers[self.BODY_BUFFER])
        self.curr_writer = old_writer

    def __semicolon(self, stmt, no_newline = False):
        """
        Write a semicolon (and newline) for all statements except the ones
        in NO_SEMICOLON.

        """
        if stmt.__class__.__name__ not in self.NO_SEMICOLON:
            self.__write(";")

    def exe_node(self, node):
        with self.Executor() as exe:
            self.visit(node)
        return exe.result

    def exe_body(self, body, skip_docstring=False, skip_global=False):
        with self.Executor() as exe:
            for stmt in body:
                """
                if skip_docstring and isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Str):
                    continue # Skip docstring
                """
                if skip_global and isinstance(stmt, ast.Global): # The `global` statement is invisible
                    self.visit(stmt)
                    continue
                self.visit(stmt)
                self.__semicolon(stmt)
        return exe.result

    def exe_first_differs(self, body, first_text=None, rest_text=None, do_visit=None):
        if do_visit is None:
            do_visit = lambda node: self.visit(node)

        with self.Executor() as exe:
            first = True
            for node in body:
                if first:
                    first = False
                    if first_text is not None:
                        self.__write(first_text)
                else:
                    if rest_text is not None:
                        self.__write(rest_text)
                do_visit(node)

        return exe.result

    def get_util_var_name(self, name, value):
        if not self.bare:
            if not name in self.util_names:
                self.util_names[name] = (self.mod_scope.generate_variable(name), value)
            varname, value = self.util_names[name]
            return varname
        else:
            return value

    def raise_error(self, message, node):
        raise ParseError(message, node.lineno, node.col_offset)


def translate_string(input,namespace=""):
    config = {}
    output = StringIO()
    config["bare"] = True
    config["input_name"] = None
    config["input_lines"] = [input]
    config["output"] = StringIO()
    config["namespace"] = namespace
    config["use_throw_helper"] = True
    config["warnings"] = False
    config["use_throw_helper"] = False

    try:
        tree = ast.parse(input)
    except SyntaxError as e:
        raise ParseError(e.msg, e.lineno, e.offset, True)

    scope_gen = PyScopeGenerator(config["namespace"], tree)

    moo = Translator(scope_gen.root_scope, config)
    moo.visit(tree)
    return config["output"].getvalue()



def translate_file(config):
    config["use_throw_helper"] = True
    try:
        tree = builder.ASTNGBuilder().string_build(config["input"], config["input_name"])
        scope_gen = PyScopeGenerator(config["namespace"], tree)
        scope_gen.visit(tree)

        moo = Translator(scope_gen.root_scope, config)
        moo.visit(tree)
        return scope_gen.root_scope.imported_modules()
    except ParseError as e:
        e.input_lines = config["input_lines"]
        e.input_name = config["input_name"]
        raise e
    except SyntaxError as e:
        raise ParseError(e.msg, e.lineno, e.offset, True, config["input_lines"], config["input_name"])



