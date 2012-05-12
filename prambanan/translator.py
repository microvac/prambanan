#!/usr/bin/env python

#
# PyCow - Python to JavaScript with MooTools translator
# Copyright 2009 Patrick Schneider <patrick.p2k.schneider@gmail.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
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

import ast, simplejson, re, random
from StringIO import StringIO
import inspect
import sys
import engine
from prambanan.context import Context
from prambanan.scope import Scope
from prambanan import ParseError, Writer

__all__ = ["translate_files"]

class Translator(ast.NodeVisitor):
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
        "Add":	("+", 6, True), # chars, precedence, associates
        "Sub":	("-", 6, True),
        "Mult":	("*", 5, True),
        "Div":	("/", 5, True),
        "FloorDiv":	("/", 5, True),
        "Mod":	("%", 5, True),
        "Pow":	("", 5, True),
        #"Pow":	?,
        "LShift":	("<<", 7, True),
        "RShift":	(">>", 7, True),
        "BitOr":	("|", 12, True),
        "BitXor":	("^", 11, True),
        "BitAnd":	("&", 10, True),

        "USub":	("-", 4, False),
        "UAdd": ("+", 4, False),

        "And":	("&&", 13, True),
        "Or":	("||", 14, True),

        "Not":	("!", 4, False),

        "Eq":	("===", 9, True),
        "Is":	("===", 9, True),
        "NotEq":("!==", 9, True),
        "Lt":	("<", 8, True),
        "LtE":	("<=", 8, True),
        "Gt":	(">", 8, True),
        "GtE":	(">=", 8, True),
        }

    NO_SEMICOLON = [
        "Global",
        "If",
        "While",
        "For",
        "TryExcept",
        "TryFinally",
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


    IDENTIFIER_RE = re.compile("[A-Za-z_$][0-9A-Za-z_$]*")

    HEADER_BUFFER = "header"
    BODY_BUFFER = "body"
    FOOTER_BUFFER = "footer"

    BUFFER_NAMES = [HEADER_BUFFER, BODY_BUFFER, FOOTER_BUFFER]

    LIB_NAME = "prambanan"

    def __init__(self, scope, config):
        self.__mod_context = scope

        self.writer_stack = []

        self.input_name = config["input_name"]
        self.input_lines = config["input_lines"]
        self.out = config["output"]
        self.namespace = config["namespace"]
        self.__warnings = config["warnings"]
        self.use_throw_helper = "use_throw_helper" in config

        self.export_map = {}
        self.public_identifiers = []
        self.translated_names = {}
        self.util_names = {}
        self.engine = engine.BackboneEngine()
        self.bare = False;

        self.__curr_context = None
        self.__iteratorid = 0

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

    def visit_Module(self, mod):
        """
        Initial node.
        There is and can be only one Module node.

        """
        self.curr_writer = Writer(self.BODY_BUFFER, self.BUFFER_NAMES)
        self.__curr_context = self.__mod_context

        if not self.bare:
            self.__change_buffer(self.HEADER_BUFFER)
            if self.__mod_context.module_license != "":
                license = self.exe_first_differs(self.__mod_context.module_license.split("\n"),
                                                first_text="/* %s\n" % (line), rest_text=" * %\n" % (line),
                                                do_visit=lambda n: self.out.write(" */\n"))
                self.__write(license)

            if self.__mod_context.docstring != "": self.__write_docstring(self.__mod_context.docstring)

            self.__write("(function(%s) {" % self.LIB_NAME)
            self.__change_buffer(self.BODY_BUFFER)

            for k, v in self.export_map.items():
                self.__mod_context.declare_variable(k)
                self.__write("%s = %s.%s;" % (k, self.LIB_NAME, v))

            if self.use_throw_helper:
                self.get_util_var_name("_throw", "%s.helpers.throw" % self.LIB_NAME)
                self.get_util_var_name("__py_file__", "'%s'" % self.input_name)

            public_identifiers = self.__mod_context.module_all
            not_all_exists = public_identifiers is None
            if not_all_exists:
                public_identifiers = []

        for stmt in mod.body:
            if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 and\
               isinstance(stmt.targets[0], ast.Name) and\
               stmt.targets[0].id in ("__all__", "__license__"):
                continue
            if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Str):
                continue # Module docstring

            if not self.bare and not_all_exists:
                name = None
                if isinstance(stmt, ast.ClassDef) or isinstance(stmt, ast.FunctionDef):
                    name = stmt.name
                if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 and\
                   isinstance(stmt.targets[0], ast.Name):
                   name = stmt.targets[0].id
                if name is not None and not name.startswith("_"):
                    public_identifiers.append(name)

            self.visit(stmt)
            if( not isinstance(stmt, ast.Import) and not isinstance(stmt, ast.ImportFrom) and not isinstance(stmt, ast.Pass)):
                self.__semicolon(stmt)

        if not self.bare:
            self.public_identifiers.extend(public_identifiers)

            get_name = lambda name: name if name not in self.translated_names else self.translated_names[name]
            exported = (self.exe_first_differs(sorted(set(self.public_identifiers)), rest_text=",",
                do_visit=lambda name: self.__write("%s: %s" % (name, get_name(name)))))

            self.__write("%s.exports('%s',{%s})(%s);" % (self.LIB_NAME, self.namespace, exported, self.LIB_NAME))
            self.__change_buffer(self.HEADER_BUFFER)

            builtin_var = None
            builtins = set(self.__mod_context.all_used_builtins())
            if len(builtins) > 0:
                builtin_var = self.__curr_context.generate_variable("__builtin__")
                for builtin in builtins:
                    self.__curr_context.declare_variable(builtin)

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
        self.__curr_context = None


    def visit_ImportFrom(self, i):
        """
        from module import itema, itemb ->
            module1 = __import__('module'); itema = module1.itema; itemb = module.itemb;
        """
        module = i.module
        if i.level == 1:
            if module is None:
                module = self.namespace
            else:
                module = self.namespace+"."+module
        modulevarname = module if "." not in module else module[0:module.find(".")]
        modulevarname = self.__curr_context.generate_variable("_m_"+modulevarname)
        self.__write("%s = __import__('%s'); " % (modulevarname, module))
        for name in i.names:
            varname = name.asname if name.asname else name.name
            self.__write("%s = %s.%s;  " % (varname, modulevarname, name.name))

    def visit_Import(self, i):
        """
        import module -> module = __import__(module)
        import namespace.module -> namespace = __import__(namespace)
        import namespace.module as alias -> alias = __import__(namespace.module)
        """
        first = True
        for name in i.names:
            importname = name.name
            varname = name.name
            if name.asname:
                varname = name.asname
            else:
                if "." in importname:
                    importname = importname[0:importname.find(".")]
                    varname = importname
            self.__write("%s = __import__('%s');" % (varname, importname))

    def visit_Call(self, c):
        """
        Translates a function/method call or class instantiation.
        every named arguments became keyword arguments
        """

        cls = self.__curr_context.class_context()

        type = None
        name = None
        call_type = None
        method_written = False
        if isinstance(c.func, ast.Name):
            if c.func.id == "JS":
                if len(c.args) != 1:
                    raise ParseError("native js only accept one argument", c.lineno, c.col_offset)
                if not isinstance(c.args[0], ast.Str):
                    raise ParseError("native js only accept string",c.lineno, c.col_offset)
                self.__write(re.sub(r'(?:@{{[!]?)([^}}]*)(?:}})', r"\1",c.args[0].s))
                return

            call_type = "name"
            if self.__curr_context.check_builtin_usage(c.func.id):
                if c.func.id in Scope.BUILTINS_FUNC:
                    type = "Function"
                else:
                    type = "Class"
            else:
                # Look in current context
                type = getattr(self.__curr_context.lookup(c.func.id), "type", None)
                name = c.func.id
        elif isinstance(c.func, ast.Attribute):
            call_type = "attr"
            name = "."+c.func.attr
            if cls is not None and isinstance(c.func.value, ast.Call) and isinstance(c.func.value.func, ast.Name) :
                name = c.func.value.func.id+name
                if c.func.value.func.id == "super":
                    # A super call
                    if (not len(c.func.value.args) == 2):
                        raise ParseError("Only python 2 simple super supported", c.lineno, c.col_offset)
                    attrname = c.func.attr
                    self.__write("%s(" % self.get_util_var_name("_super", "%s.helpers.super" % self.LIB_NAME))
                    self.__write("this, '%s')" %  attrname)
                    method_written = True
                    type = "Function"
            elif isinstance(c.func.value, ast.Name) and c.func.value.id == "self":
                # Look in Class context
                if cls is not None:
                    type = getattr(cls.child(c.func.attr), "type", None)
            else:
                # Create attribute chain
                attrlst = [c.func.attr]
                value = c.func.value
                while isinstance(value, ast.Attribute):
                    name = value.attr+name
                    attrlst.append(value.attr)
                    value = value.value
                if isinstance(value, ast.Name): # The last value must be a Name
                    name = value.id+name
                    ctx = self.__curr_context.lookup(value.id)
                    while ctx is not None: # Walk up
                        ctx = ctx.child(attrlst.pop())
                        if ctx is not None and len(attrlst) == 0: # Win
                            type = ctx.type
                            break
                    if type is None:
                            imports = self.__curr_context.all_imports()
                            if value.id in imports:
                                importname, varname = imports[value.id]
                                try:
                                    __import__(importname)
                                    obj = sys.modules[importname]
                                    if varname is not None: obj = getattr(obj, varname)
                                    attrError = False
                                    for attr in reversed(attrlst):
                                        try:
                                            obj = getattr(obj, attr)
                                        except AttributeError:
                                            print "attr error"
                                            attrError = True
                                            break
                                    if not attrError:
                                        if inspect.isfunction(obj) or inspect.ismethod(obj):
                                            type = "Function"
                                        elif inspect.isclass(obj):
                                            type = "Class"
                                except AttributeError:
                                    print "attr after import error"
                                except ImportError:
                                    print "import error"


        if type is None and "type" in self.__warnings:
            sys.stderr.write(" Warning: Cannot infer type [ call: %s, name: %s ] in line %s\n" % (call_type, name, c.lineno ))
        elif type == "Class":
            self.__write("new ")

        if not method_written:
            self.visit(c.func)
        self.__write("(")
        self.__parse_args(c)
        self.__write(")")

    def visit_Name(self, n):
        """
        Translate an identifier. If the context is a method, substitute `self`
        with `this`.

        Some special keywords:
        True -> true
        False -> false
        None -> null

        """
        if self.__curr_context.type == "Method" and n.id == "self":
            self.__write("this")
        elif n.id == "True" or n.id == "False":
            self.__write(n.id.lower())
        elif n.id == "None":
            self.__write("null")
        elif n.id in self.RESERVED_WORDS:
            if not n.id in self.translated_names:
                self.translated_names[n.id] = self.__mod_context.generate_variable("__keyword_"+n.id)
            self.__write(self.translated_names[n.id])
        else:
            self.__write(n.id)

    def visit_BinOp(self, o):
        """
        Translates a binary operator.
        Note: The modulo operator on strings is translated to left.sprintf(right)
        and currently the only spot where tuples are allowed.

        """
        if isinstance(o.left, ast.Str) and isinstance(o.op, ast.Mod):
            args = self.exe_first_differs(o.right.elts, rest_text=",") if isinstance(o.right, ast.Tuple) else self.exe_node(o.right)
            self.__write("%s.sprintf(%s)" % (self.exe_node(o.left), args))
        elif isinstance(o.op, ast.Pow):
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

    def visit_BoolOp(self, o):
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

    def visit_UnaryOp(self, o):
        """
        Translates a unary operator.

        """
        self.__write(self.__get_op(o.op))
        prec, assoc = self.__get_expr_pa(o.operand)
        if isinstance(o.operand, ast.Num): prec = 3
        if prec > 2: self.__write("(")
        self.visit(o.operand)
        if prec > 2: self.__write(")")

    def visit_Compare(self, c):
        """
        Translate a compare block.

        """
        if len(c.ops) > 1:
            raise ParseError("Comparisons with more than one operator are not supported", c.lineno, c.col_offset)

        op, expr = c.ops[0], c.comparators[0]

        if not isinstance(op, ast.In) and not isinstance(op, ast.NotIn):
            self.visit(c.left)

        if isinstance(op, ast.IsNot) and expr.id == "None":
            self.__write(" !== .null")
        elif isinstance(op, ast.In) or isinstance(op, ast.NotIn):
            if isinstance(op, ast.NotIn):
                self.__write(" !")
            in_helper = self.get_util_var_name("_in", "%s.helpers.in"%self.LIB_NAME)
            self.__write(" %s(%s, %s) " % (in_helper, self.exe_node(c.left), self.exe_node(expr)))
        else:
            self.__write(" %s " % (self.__get_op(op)))
            prec, assoc = self.__get_expr_pa(expr)
            if prec > 2: self.__write("(")
            self.visit(expr)
            if prec > 2: self.__write(")")

    def visit_Dict(self, d):
        """
        Translate a dictionary expression.

        """
        with self.Executor() as items:
            first = True
            for i in xrange(len(d.keys)):
                key, value = d.keys[i], d.values[i]
                if first:
                    first = False
                else:
                    self.__write(",")
                if isinstance(key, ast.Num):
                    self.__write("%d: " % (key.n))
                elif not isinstance(key, ast.Str):
                    raise ParseError("Only numbers and string literals are allowed in dictionary expressions", key.lineno, key.col_offset)
                else:
                    if self.IDENTIFIER_RE.match(key.s):
                        self.__write("%s: " % (key.s))
                    else:
                        self.__write("\"%s\": " % (key.s))
                self.visit(value)
        self.__write("{%s}" % items.result)

    def visit_Subscript(self, s):
        """
        Translate a subscript expression.

        """

        #   optimize simple index slice
        if isinstance(s.ctx, ast.Load) or isinstance(s.ctx, ast.Assign) or isinstance(s.ctx, ast.Store) :
            if isinstance(s.slice, ast.Index) and isinstance(s.slice.value, ast.Num) and s.slice.value.n >= 0:
                self.__write('%s[%s]' % (self.exe_node(s.value), self.exe_node(s.slice.value)))
                return

        func = ""
        if isinstance(s.ctx, ast.Load):
            func = "load"
        elif isinstance(s.ctx, ast.Del):
            func = "del"
        elif isinstance(s.ctx, ast.Assign):
            func = "assign"
        elif isinstance(s.ctx, ast.Store):
            func = "assign"
        else:
            raise ParseError("Subscript with context '%s' is not supported" % (str(s.ctx.__class__.__name__)), s.lineno, s.col_offset)

        self.__write("%s('%s'," % (self.get_util_var_name("_subscript", ("%s.helpers.subscript" % self.LIB_NAME)), func))
        self.visit(s.value)
        self.__write(", ")
        if isinstance(s.slice, ast.Index):
            self.__write("'index', ")
            self.visit(s.slice.value)
        elif isinstance(s.slice, ast.Slice):
            self.__write("'slice', ")
            if s.slice.lower is not None:
                self.visit(s.slice.lower)
            else:
                self.__write("null")
            self.__write(", ")
            if s.slice.upper is not None:
                self.visit(s.slice.upper)
            else:
                self.__write("null")
            self.__write(", ")
            if s.slice.step is not None:
                self.visit(s.slice.step)
            else:
                self.__write("null")
        else:
            raise ParseError("Subscript slice type '%s' is not supported" % (str(s.slice.__class__.__name__)), s.lineno, s.col_offset)
        self.__write(")")

    def visit_Assign(self, a):
        """
        Translate an assignment.
        if target is tuple, became self executable function:
            (a, b) = c
                =>
                (function(_source){ a = _source[0]; b = _source[1]})(c);
        if value is tuple make array:
            c = (a, b)
                => c = [a, b]

        """
        is_class = self.__curr_context.type == "Class"

        if len(a.targets) > 1 and is_class:
            raise ParseError("Cannot handle multiple assignment on class context", a.targets[0].lineno, a.targets[1].col_offset)

        is_target_tuple = False
        tuple_target = None
        for target in a.targets:
            if isinstance(target, ast.Tuple):
                is_target_tuple = True
                tuple_target = target

        if is_target_tuple and len(a.targets) > 1:
            raise ParseError("tuple are not allowed on multiple assignment", tuple_target.lineno, tuple_target.col_offset)

        if is_target_tuple and is_class:
            raise ParseError("tuple assignment are not allowed on class scope", tuple_target.lineno, tuple_target.col_offset)

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
                if is_class and not isinstance(target, ast.Name):
                    raise ParseError("Only simple variable assignments are allowed on class scope", target.lineno, target.col_offset)
                self.visit(target)
                if is_class:
                    self.__write(": ")
                else:
                    self.__write(" = ")

        if isinstance(a.value, ast.Tuple):
            self.__write("[%s]" % self.exe_first_differs(a.value.elts, rest_text=","))
        else:
            self.visit(a.value)
        if is_target_tuple:
            self.__write(")")

    def visit_AugAssign(self, a):
        """
        Translate an assignment operator.

        """
        self.visit(a.target)
        if isinstance(a.value, ast.Num) and a.value.n == 1:
            if isinstance(a.op, ast.Add):
                self.__write("++")
                return
            elif isinstance(a.op, ast.Sub):
                self.__write("--")
                return
        self.__write(" %s= " % (self.__get_op(a.op)))
        self.visit(a.value)

    def visit_For(self, f):
        """
        Translate a for loop.

        """

        # -- This solution is needed to keep all semantics --
        #
        # for (var __iter0_ = new XRange(start, stop, step); __iter0_.hasNext();) {
        #     var value = __iter0_.next();
        #
        # }
        # delete __iter0_;
        #
        # for (var __iter0_ = new _Iterator(expr); __iter0_.hasNext();)) {
        #     var value = __iter0_.next();
        #     var key = __iter0_.key();
        # }
        # delete __iter0_;


        i_var = self.__curr_context.generate_variable("_i")
        len_var = self.__curr_context.generate_variable("_len")
        is_tuple = False
        iter_var = None

        if isinstance(f.target, ast.Name):
            iter_var = f.target.id
        else:
            is_tuple = True
            iter_var = []
            for elt in f.target.elts:
                t = elt.id
                iter_var.append(t)

        list_var = self.__curr_context.generate_variable("_list")
        init = ""

        if not is_tuple:
            init = ("%s = %s[%s];" % (iter_var, list_var, i_var))
        else:
            for i in range(0, len(iter_var)):
                init = init + ("%s = %s[%s][%d];" % (iter_var[i], list_var, i_var, i))

        self.__write("%s = %s;" % (list_var, self.exe_node(f.iter)))
        self.__write("for (%s = 0, %s = %s.length; %s < %s; %s++) {" % (i_var, len_var, list_var, i_var, len_var, i_var))
        self.__write(" %s" % init)
        self.__write(" %s" % self.exe_body(f.body))
        self.__write("}")
        if len(f.orelse) > 0:
            self.__write("if(%s == %s){%s}" % (i_var, len_var, self.exe_body(f.orelse)))

        self.__iteratorid -= 1

    def visit_ClassDef(self, c):
        """
        Translates a Python class into a MooTools class.
        This inserts a Class context which influences the translation of
        functions and assignments.

        """
        fullname = "t__%s_" % c.name if self.namespace == "" else "t_%s_%s" % (self.namespace.replace(".", "_"), c.name)
        ctor_name = self.__curr_context.generate_variable("%s" % fullname)
        self.__push_context(c.name)

        self.__change_buffer(self.HEADER_BUFFER)

        # Write docstring
        if len(self.__curr_context.docstring) > 0:
            self.__write_docstring(self.__curr_context.docstring)

        self.__write("function %s(){ this.__init__.apply(this, arguments); } " % (ctor_name))
        self.__write("%s = " % (c.name))

        decorators = self.__get_decorators(c)
        if decorators.has_key("Export"):
            for expr in decorators["Export"]:
                self.__write("%s.%s = " % (expr.s, c.name))

        if len(c.bases) > 1 :
            raise ParseError("Could not do multiple inheritance",  c.lineno, c.bases[1].col_offset)

        bases = filter(lambda b: not isinstance(b, ast.Name) or b.id != "object", c.bases)
        if len(bases) > 0:
            self.visit(bases[0])
        else:
            self.__write("object")

        self.__write(".extend({constructor: %s" % ctor_name)

        self.__change_buffer(self.BODY_BUFFER)
        # Base classes
        first_docstring = True
        statics = []
        for stmt in c.body:
            if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Str):
                if first_docstring:
                    first_docstring = False
                else:
                    self.__write_docstring(stmt.value.s)
                continue
            if isinstance(stmt, ast.FunctionDef):
                if self.__get_decorators(stmt).has_key("staticmethod"):
                    statics.append(stmt)
                    continue
            if not isinstance(stmt, ast.Pass):
                self.__write(",")
            self.visit(stmt)

        if len(statics) > 0:
            self.__write("/* static methods */")
            self.__write("},{%s}" %self.exe_first_differs(statics, rest_text=","))
        self.__write(")")

        self.__pop_context()

    def visit_FunctionDef(self, f):
        """
        Translate a Python function into a JavaScript function.
        Depending on the context, it is translated to `var name = function (...)`
        or `name: function (...)`.

        """
        self.__push_context(f.name)
        self.__change_buffer(self.HEADER_BUFFER)

        is_method = self.__curr_context.type == "Method"

        # Special decorators
        decorators = self.__get_decorators(f)
        is_static = decorators.has_key("staticmethod")

        # Write docstring
        if len(self.__curr_context.docstring) > 0:
            self.__write_docstring(self.__curr_context.docstring)
        if is_method:
            self.__write("%s: function (" % (f.name))
        else:
            self.__write("%s = function (" % (f.name))

        # Parse arguments
        self.__parse_args(f.args, is_method and not is_static)
        self.__write(") {")

        # Parse defaults
        self.__parse_defaults(f.args)

        self.__change_buffer(self.BODY_BUFFER)
        if "JSNoOp" in decorators:
            self.__write("return undefined;")
        else:
            self.__write(self.exe_body(f.body, True, True))
        self.__write("}")
        self.__pop_context()


    def visit_TryExcept(self, tf):
        ex_var = self.__curr_context.generate_variable("_ex")

        self.__write("try{ %s }" % self.exe_body(tf.body, True, True))
        self.__write("catch (%s){" % ex_var)
        has_first = False
        has_catch_all = False
        for handler in tf.handlers:
            has_if = False
            if handler.type is not None:
                if has_first:
                    self.__write("else ")
                if(isinstance(handler.type, ast.Attribute) or isinstance(handler.type, ast.Name)):
                    self.__write("if (%s instanceof %s){" %(ex_var, self.exe_node(handler.type)))
                elif(isinstance(handler.type, ast.Tuple)):
                    self.__write("if (%s){" % self.exe_first_differs(handler.type.elts,
                        rest_text="||",
                        do_visit=lambda elt: self.__write("(%s instanceof %s)" % (ex_var, self.exe_node(elt)))
                    ))
                has_if = has_first = True
            else:
                has_catch_all = True
                if has_first:
                    self.__write("else {")
                    has_if = True
                has_first = True
            if handler.name is not None:
                self.__write("%s = %s;" %(handler.name.id, ex_var))
            self.__write(self.exe_body(handler.body, True, True))
            if has_if:
                self.__write("}");
        if not has_catch_all:
            if has_first:
                self.__write("else { throw %s;}" % ex_var)
        self.__write("}");

    def visit_ListComp(self, lc):
        """
        [expr for item if expr in lists] ->
            (function(){
                var _i, _len, _results;
                _results = []
            })();
        """
        if len(lc.generators) > 1:
            raise ParseError("Could only support one generator now",  lc.generators[1].target.lineno, lc.generators[1].target.col_offset)

        f = lc.generators[0]

        is_tuple = False
        iter_var = None

        if isinstance(f.target, ast.Name):
            iter_var = f.target.id
        else:
            is_tuple = True
            iter_var = []
            for elt in f.target.elts:
                t = elt.id
                iter_var.append(t)

        self.__push_context(lc.name)
        self.__change_buffer(self.HEADER_BUFFER)
        self.__write(" (function(){ ")
        self.__change_buffer(self.BODY_BUFFER)

        i_var = self.__curr_context.generate_variable("_i")
        len_var = self.__curr_context.generate_variable("_len")
        results_var = self.__curr_context.generate_variable("_results")

        list_var = self.__curr_context.generate_variable("_list")
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
            self.__write("    if (%s)" % self.exe_node(e_if))
        self.__write(            "%s.push(%s);" % (results_var, self.exe_node(lc.elt)))
        self.__write("}")
        self.__write("return %s;" % results_var)
        self.__write("})()")

        self.__pop_context()


    def visit_Raise(self, r):
        type = self.exe_node(r.type)

        if self.use_throw_helper:
            throw, how = self.util_names["_throw"]
            file, how = self.util_names["__py_file__"]
            self.__write("%s(%s, %s, %d)"% (throw, type, file, r.lineno))
        else:
            self.__write("throw %s" % type)

    def visit_Print(self, p):
        """
        Translate print "aa" to print("aa")

        """
        self.__write("print(%s)" % self.exe_first_differs(p.values, rest_text=","))

    def visit_Num(self, n):
        self.__write(str(n.n))

    def visit_Str(self, s):
        """
        Output a quoted string.
        Cleverly uses JSON to convert it ;)

        """
        self.__write(simplejson.dumps(s.s))


    def visit_Expr(self, expr):
        self.visit(expr.value)


    def visit_Global(self, g):
        """
        Declares variables as global.

        """
        pass

    def visit_Lambda(self, l):
        """
        Translates a lambda function.

        """
        self.__write("function (")
        self.__parse_args(l.args)
        self.__write(") {return %s; }" % self.exe_node(l.body))

    def visit_Yield(self, y):
        """
        Translate the yield operator.

        """
        self.__write("yield %s" % self.exe_node(y.value))

    def visit_Return(self, r):
        """
        Translate the return statement.

        """
        if r.value:
            self.__write("return %s" % self.exe_node(r.value))
        else:
            self.__write("return")

    def visit_List(self, l):
        """
        Translate a list expression.

        """
        self.__write("[%s]" % self.exe_first_differs(l.elts, rest_text=","))

    def visit_Delete(self, d):
        """
        Translate a delete statement.

        """
        for target in d.targets:
            if isinstance(target, ast.Subscript):
                self.visit(target)
            else:
                self.__write("delete %s" % self.exe_node(target))


    def visit_Pass(self, p):
        """
        Translate the `pass` statement. Places a comment.

        """
        self.__write("/* pass */")

    def visit_Continue(self, c):
        """
        Translate the `continue` statement.

        """
        self.__write("continue")

    def visit_Break(self, c):
        """
        Translate the `break` statement.

        """
        self.__write("break")

    def visit_Attribute(self, a):
        """
        Translate an attribute chain.

        """
        self.__write("%s.%s" % (self.exe_node(a.value), a.attr))

    def visit_If(self, i):
        """
        Translate an if-block.

        """
        self.__write("if ( %s ) { %s }" % (self.exe_node(i.test), self.exe_body(i.body)))
        if len(i.orelse) > 0:
            self.__write("else {%s}" % self.exe_body(i.orelse))


    def visit_IfExp(self, i):
        """
        Translate an if-expression.

        """
        self.__write("%s ? %s : %s" % (self.exe_node(i.test), self.exe_node(i.body), self.exe_node(i.orelse)))

    def visit_While(self, w):
        """
        Translate a while loop.

        """
        if len(w.orelse) > 0:
            raise ParseError("`else` branches of the `while` statement are not supported", w.orelse[0].lineno, w.orelse[0].col_offset)

        self.__write("while (%s){ %s }" % (self.exe_node(w.test), self.exe_body(w.body)))



    def visit_TryFinally(self, tf):
        self.__write("try{ %s } finally { %s }" (self.exe_body(tf.body, True, True) % self.exe_body(tf.finalbody, True, True)))

    def visit_Assert(self, a):
        pass

    def visit_Tuple(self, t):
        self.__write("[%s]" % self.exe_first_differs(t.elts, rest_text=","))

    def generic_visit(self, node):
        raise ParseError("Could not parse node type '%s'" % str(node.__class__.__name__), node.lineno, node.col_offset)

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
        #if getattr(args, "vararg", None) is not None:
        #    raise ParseError("Variable arguments on function definitions are not supported")

    def __parse_defaults(self, args):
        """
        Translate the default arguments list.
            (a, b) -> (a, b)
            (a, b=3)-> (a, b)
                        if(_.isUndefined(b)) a = 3;
            (a, b=3, *args)-> (a, b)->
                        if(_.isUndefined(b)) a = 3;
                        args = Prambanan.varargs(arguments, 2) // 2 is non var args variablej
            (a, b=3, **kwargs) ->
                    args = Prambanan.kwargs(arguments, 2)
        """
        if len(args.defaults) > 0:
            first = len(args.args) - len(args.defaults)
            for i in xrange(len(args.defaults)):
                self.__write("if (%s(" % self.get_util_var_name("_isUndefined", ("%s.helpers._.isUndefined" % self.LIB_NAME)))

                self.visit(args.args[first+i])
                self.__write(")) ")
                self.visit(args.args[first+i])
                self.__write(" = ")
                #change to prambanan default args
                self.visit(args.defaults[i])
                self.__write(";")

    def __get_decorators(self, stmt):
        """
        Return a dictionary of decorators and their parameters.

        """
        decorators = {}
        if isinstance(stmt, ast.FunctionDef):
            for dec in stmt.decorator_list:
                if isinstance(dec, ast.Name):
                    if dec.id == "staticmethod":
                        decorators["staticmethod"] = []
                        continue
                    if dec.id == "JSNoOp":
                        decorators["JSNoOp"] = []
                        continue
                raise ParseError("This function decorator is not supported. Only @staticmethod is supported for now.", dec.lineno, dec.col_offset)
        else:
            for dec in stmt.decorator_list:
                if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Name):
                    if dec.func.id == "Implements":
                        decorators["Implements"] = dec.args
                        continue
                    if dec.func.id == "Export":
                        decorators["Export"] = dec.args
                        continue
                if isinstance(dec, ast.Name) and dec.id == "Class":
                    decorators["Class"] = []
                    continue
                raise ParseError("This class decorator is not supported. Only decorators of pycow.decorators are supported",dec.lineno, dec.col_offset)
        return decorators

    def __get_op(self, op):
        """
        Translates an operator.

        """
        return self.OP_MAP[op.__class__.__name__][0]

    def __get_op_cpa(self, op):
        """
        Get operator chars, precedence and associativity.

        """
        return self.OP_MAP[op.__class__.__name__]

    def __get_expr_pa(self, expr):
        """
        Get the precedence and associativity of an expression.

        """
        if isinstance(expr, ast.Expr):
            expr = expr.value
        name = expr.__class__.__name__
        if name in ("BoolOp", "BinOp", "UnaryOp"):
            return self.__get_op_cpa(expr.op)[1:]
        elif name in ("Lambda", "Dict", "List", "Num", "Str", "Name"):
            return (1, False)
        elif name == "IfExp":
            return (15, False)
        elif name in ("Attribute", "Subscript"):
            return (1, True)
        elif name in ("Call", "Repr"):
            return (2, True)
        elif name == "Compare":
            return (8, True)

    def __change_buffer(self, buffer_name):
        self.curr_writer.change_buffer(buffer_name)

    def __write(self, s):
        self.curr_writer.write(s)

    def __write_docstring(self, s):
        self.__write("/**\n")
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
        if len(self.__curr_context.variables) > 0:
            first = True
            for variable in sorted(self.__curr_context.variables):
                if first:
                    self.__write("var ")
                    first = False
                else:
                    self.__write(", ")
                self.__write(variable)
            self.__write(";")



    def __push_context(self, identifier):
        """
        Walk context up.

        """
        old_context = self.__curr_context
        self.__curr_context = self.__curr_context.child(identifier)
        if self.__curr_context is None:
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
        is_class = self.__curr_context.type == "Class"

        if not is_class:
            self.__write_variables()
        self.__curr_context = self.__curr_context.parent

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

    def __build_namespace(self, namespace):
        namespace = namespace.split(".")

        self.__write("window.%s = %s._.isUndefined(window.%s) ? {} : window.%s;" % (self.LIB_NAME, namespace[0], namespace[0], namespace[0]))

        for i in xrange(1, len(namespace) - 1):
            self.__write("%s.%s = %s._.isUndefined(%s.%s) ? {} : %s.%s;" % (self.LIB_NAME, namespace[i-1], namespace[0], namespace[i-1], namespace[0], namespace[i-1], namespace[0]))

    def exe_node(self, node):
        with self.Executor() as exe:
            self.visit(node)
        return exe.result

    def exe_body(self, body, skip_docstring=False, skip_global=False):
        with self.Executor() as exe:
            for stmt in body:
                if skip_docstring and isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Str):
                    continue # Skip docstring
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
        if not name in self.util_names:
            self.util_names[name] = (self.__mod_context.generate_variable(name), value)
        varname, value = self.util_names[name]
        return varname


def translate_files(config):
    config["use_throw_helper"] = True
    try:
        tree = ast.parse(config["input"], config["input_name"])
    except SyntaxError as e:
        raise ParseError(e.msg, e.lineno, e.offset, True)

    context = Context(config["namespace"], tree)

    moo = Translator(context.root_scope, config)
    moo.visit(tree)


