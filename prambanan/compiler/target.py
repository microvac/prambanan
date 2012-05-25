import simplejson, re
import sys

from logilab.astng import nodes

from prambanan.compiler.translator import BaseTranslator
from prambanan.compiler.utils import ParseError, Writer

import utils

class Targets(object):
    __default = None
    __targets = {}

    def get_translator(self, name):
        return self.__targets.get(name, self.__default)

    def default(self, cls):
        self.__default = cls
        return cls

    def register(self, name):
        def dec(cls):
            self.__targets[cls] = name
            return cls
        return dec

targets = Targets()

@targets.default
class JSDefaultTranslator(BaseTranslator):
    """
    Second-pass main parser.

    generated variable names:
        Prambanan.in, Prambanan.subscript, Prambanan.undescore -> same
        module in import from -> _m_
        builtins -> same name
        iterator -> _i, _source, _len, etc
        ex -> _ex


"""
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
        self.write("%s = __import__('%s'); " % (modulevarname, module))
        for name,asname in i.names:
            varname = asname if asname else name
            self.write("%s = %s.%s;  " % (varname, modulevarname, name))

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
            self.write("%s = __import__('%s');" % (varname, importname))

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
        if isinstance(c.func, nodes.Name):
            call_type = "name"
            if c.func.name == "JS":
                if len(c.args) != 1:
                    raise ParseError("native js only accept one argument", c.lineno, c.col_offset)
                if not isinstance(c.args[0], nodes.Const) and not isinstance(c.args[0].value, str):
                    raise ParseError("native js only accept string",c.lineno, c.col_offset)
                self.write(re.sub(r'(?:@{{[!]?)([^}}]*)(?:}})', r"\1",c.args[0].value))
                return
        elif isinstance(c.func, nodes.Getattr):
            call_type = "getattr"
            if cls is not None and isinstance(c.func.expr, nodes.CallFunc) and isinstance(c.func.expr.func, nodes.Name) :
                if c.func.expr.func.name == "super":
                    # A super call
                    if (not len(c.func.expr.args) == 2):
                        self.raise_error("Only python 2 simple super supported", c)
                    attrname = c.func.attrname
                    self.write("%s(" % self.get_util_var_name("_super", "%s.helpers.super" % self.LIB_NAME))
                    self.write("this, '%s')" %  attrname)
                    method_written = True

        if type is None and "type" in self.warnings:
            sys.stderr.write(" Warning: Cannot infer type [ call: %s, name: %s ] in line %s\n" % (call_type, name, c.lineno ))
        elif type == "Class":
            self.write("new ")

        if not method_written:
            self.visit(c.func)
        self.write("(")
        self.write_call_args(c)
        self.write(")")

    def visit_assname(self, n):
        self.visit_name(n)

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
        if n.name in utils.RESERVED_WORDS:
            if not n.name in self.translated_names:
                self.translated_names[n.name] = self.mod_scope.generate_variable("__keyword_"+n.name)
            self.write(self.translated_names[n.name])
        else:
            self.write(n.name)

    def visit_binop(self, o):
        """
        Translates a binary operator.
        Note: The modulo operator on strings is translated to left.sprintf(right)
        and currently the only spot where tuples are allowed.

        """
        if o.op == "%" and not (isinstance(o.left, nodes.Const) and isinstance(o.left.value, int)):
            args = self.exe_first_differs(o.right.elts, rest_text=",") if isinstance(o.right, nodes.Tuple) else self.exe_node(o.right)
            self.write("%s.__mod__(%s)" % (self.exe_node(o.left), args))
        elif o.op == "**":
            pow_helper = self.get_util_var_name("_pow", "%s.helpers.pow" % self.LIB_NAME)
            self.write("%s(%s, %s)" % (pow_helper, self.exe_node(o.left), self.exe_node(o.right)))
        else:
            chars, prec, assoc = utils.get_op_cpa(o.op)
            self.visit(o.left)
            self.write(" %s " % (chars))
            eprec, eassoc = utils.get_expr_pa(o.right)
            if eprec >= prec: self.write("(")
            self.visit(o.right)
            if eprec >= prec: self.write(")")

    def visit_boolop(self, o):
        """
        Translates a boolean operator.

        """
        first = True
        chars, prec, assoc = utils.get_op_cpa(o.op)
        for expr in o.values:
            if first:
                first = False
            else:
                self.write(" %s " % (utils.get_op(o.op)))
            eprec, eassoc = utils.get_expr_pa(expr)
            if eprec >= prec: self.write("(")
            self.visit(expr)
            if eprec >= prec: self.write(")")

    def visit_unaryop(self, o):
        """
        Translates a unary operator.

        """
        self.write(utils.get_op(o.op))
        prec, assoc = utils.get_expr_pa(o.operand)
        if isinstance(o.operand, nodes.Const): prec = 3
        if prec > 2: self.write("(")
        self.visit(o.operand)
        if prec > 2: self.write(")")

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
                self.write("(")

            if remaining[0] > 1:
                if not isinstance(expr, nodes.Const) and not isinstance(expr, nodes.Name):
                    right_text = self.curr_scope.generate_variable("_op")
                    inits.append("%s = %s;"% (right_text, self.exe_node(expr)))
                else:
                    right_text = self.exe_node(expr)
            else:
                right_text = self.exe_node(expr)

            if op != "in" and op != "not in":
                self.write(left_text[0])

            if op == "in" or op == "not in":
                if op == "not in":
                    self.write(" !")
                in_helper = self.get_util_var_name("_in", "%s.helpers.in"%self.LIB_NAME)
                self.write(" %s(%s, %s) " % (in_helper, left_text[0], right_text))
            else:
                self.write(" %s " % (utils.get_op(op)))
                prec, assoc = utils.get_expr_pa(expr)
                if prec > 2: self.write("(")
                self.write(right_text)
                if prec > 2: self.write(")")
            left_text[0] = right_text
            remaining[0] = remaining[0] - 1
            if len(c.ops) > 1:
                self.write(")")

        body = self.exe_first_differs(c.ops, rest_text="&&", do_visit=op_executor)
        c.inits = inits
        self.write(body)

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
                    self.write(",")
                if not isinstance(key, nodes.Const):
                    self.raise_error("Only numbers and string literals are allowed in dictionary expressions", key)
                if isinstance(key.value, int):
                    self.write("%d: " % (key.value))
                else:
                    if utils.IDENTIFIER_RE.match(key.value):
                        self.write("%s: " % (key.value))
                    else:
                        self.write("\"%s\": " % (key.value))
                self.visit(value)
        self.write("{%s}" % items.result)

    def visit_subscript(self, s):
        """
        Translate a subscript expression.

        """

        #   optimize simple index slice
        if isinstance(s.parent, nodes.Assign) or isinstance(s.parent, nodes.Discard):# or isinstance(s.parent, ast.Load) or isinstance(s.parent, ast.Store) :
            if isinstance(s.slice, nodes.Index) and isinstance(s.slice.value, nodes.Const) and s.slice.value.value >= 0:
                s.simple = True
                self.write('%s[%s]' % (self.exe_node(s.value), self.exe_node(s.slice.value)))
                return
            if isinstance(s.slice, nodes.Index) and isinstance(s.slice.value, nodes.Const) and isinstance(s.slice.value.value, str) :
                s.simple = True
                self.write('%s[%s]' % (self.exe_node(s.value), self.exe_node(s.slice.value)))
                return

        func = ""
        s.simple = True
        if isinstance(s.parent, nodes.Delete):
            func = "d"
        elif isinstance(s.parent, nodes.Assign) and s in s.parent.targets:
            func = "s"
            s.simple = False
        else:
            func = "l"

        subscript = self.get_util_var_name("_subscript", ("%s.helpers.subscript" % self.LIB_NAME))
        value = self.exe_node(s.value)
        with self.Executor() as args:
            if isinstance(s.slice, nodes.Index):
                type='i'
                self.write("%s" % ("null" if s.slice.value is None else self.exe_node(s.slice.value)))
            elif isinstance(s.slice, nodes.Slice):
                type="s"
                self.write("%s" % ("null" if s.slice.lower is None else self.exe_node(s.slice.lower)))
                self.write(", %s" % ("null" if s.slice.upper is None else self.exe_node(s.slice.upper)))
                self.write(", %s" % ("null" if s.slice.step is None else self.exe_node(s.slice.step)))
            else:
                self.raise_error("Subscript slice type '%s' is not supported" % (str(s.slice.__class__.__name__)), s)

        self.write("%s.%s.%s(%s,%s" % (subscript, func, type, value, args.result))

        if s.simple:
            self.write(")")

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
            if isinstance(target, nodes.Tuple):
                is_target_tuple = True
                tuple_target = target

        if is_target_tuple and len(a.targets) > 1:
            self.raise_error("tuple are not allowed on multiple assignment", tuple_target)

        if is_target_tuple:
            self.write("(function(_source){")
            tuple = a.targets[0]
            for i in range(0, len(target.elts)):
                elt = tuple.elts[i]
                self.visit(elt)
                self.write(" = _source[%d]; " % i)
            self.write("})(")
        else:
            for target in a.targets:
                self.visit(target)
                if isinstance(target, nodes.Subscript) and not target.simple:
                    self.write(", ")
                else:
                    self.write(" = ")

        if isinstance(a.value, nodes.Tuple):
            self.write("[%s]" % self.exe_first_differs(a.value.elts, rest_text=","))
        else:
            self.visit(a.value)

        if is_target_tuple:
            self.write(")")
        if isinstance(target, nodes.Subscript) and not target.simple:
            self.write(")")

    def visit_augassign(self, a):
        """
        Translate an assignment operator.

        """
        self.visit(a.target)
        if isinstance(a.value, nodes.Const) and a.value == 1:
            if isinstance(a.op, nodes.Add):
                self.write("++")
                return
            elif isinstance(a.op, nodes.Sub):
                self.write("--")
                return
        self.write(" %s= " % (utils.get_op(a.op[:-1])))
        self.visit(a.value)

    def visit_for(self, f):
        """
        Translate a for loop.

        """
        i_var = self.curr_scope.generate_variable("_i")
        len_var = self.curr_scope.generate_variable("_len")
        is_tuple = False

        if isinstance(f.target, nodes.AssName):
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

        self.write("%s = %s;" % (list_var, self.exe_node(f.iter)))
        self.write("for (%s = 0, %s = %s.length; %s < %s; %s++) {" % (i_var, len_var, list_var, i_var, len_var, i_var))
        self.write("   %s" % init)
        self.write("   %s" % self.exe_body(f.body))
        self.write("}")
        if len(f.orelse) > 0:
            self.write("if(%s == %s){%s}" % (i_var, len_var, self.exe_body(f.orelse)))


    def visit_class(self, c):
        """
        Translates a Python class into Javascript class
        This inserts a Class context which influences the translation of
        functions and assignments.

        """
        fullname = "t__%s_" % c.name if self.namespace == "" else "t_%s_%s" % (self.namespace.replace(".", "_"), c.name)
        ctor_name = self.curr_scope.generate_variable("%s" % fullname, declared=False)
        self.push_context(c.name)

        bases = filter(lambda b: not isinstance(b, nodes.Name) or b.name != "object", c.bases)
        if len(bases) > 0:
            bases_param = "[%s]" % self.exe_first_differs(bases, rest_text=", ")
        else:
            bases_param = "[object]"

        self.change_buffer(self.HEADER_BUFFER)


        # Named constructor function
        self.write("function %s(){ this.__init__.apply(this, arguments); } " % (ctor_name))
        if c.doc:
            self.write_docstring(c.doc)
        create_class = self.get_util_var_name("_class", "%s.helpers.class" %self.LIB_NAME)
        self.write("%s = %s(%s, %s, function(){" % (c.name, create_class, ctor_name, bases_param))


        self.change_buffer(self.BODY_BUFFER)

        exported = []
        proto_only = []
        cls_only = []
        # Instance member
        for stmt in c.body:
            exported.extend(self.get_identifiers(stmt))
            if isinstance(stmt, nodes.Function):
                decorators = self.get_special_decorators(stmt)
                if not "staticmethod" in decorators:
                    proto_only.append(stmt.name)
                else:
                    cls_only.append(stmt.name)

            self.visit(stmt)
            self.write_semicolon(stmt);

        all_attrs = set(exported).difference(set(proto_only)).difference(set(cls_only))

        def write_attrs(attrs):
            content = self.exe_first_differs(attrs, rest_text = ",", do_visit = lambda(x): self.write("%s:%s" %(x, x)))
            self.write("{%s}"% content)

        content = self.exe_first_differs([proto_only, cls_only, all_attrs], rest_text = ",", do_visit = lambda(x): write_attrs(x))
        self.write("return [%s]" % content)


        self.write("})")
        self.write_decorators(c)

        self.pop_context()

    def visit_function(self, f):
        """
        Translate a Python function into a JavaScript function.
        Depending on the context, it is translated to `var name = function (...)`
        or `name: function (...)`.

        """
        self.push_context(f.name)


        is_method = self.curr_scope.type == "Method"

        # Special decorators
        decorators = self.get_special_decorators(f)
        is_static = decorators.has_key("staticmethod")

        self.change_buffer(self.HEADER_BUFFER)

        # Write docstring
        if f.doc:
            self.write_docstring(f.doc)

        # Declaration
        self.write("%s = function (" % f.name)

        # Parse arguments
        self.write_def_args(f.args, is_method and not is_static)
        self.write(") {")

        self.change_buffer(self.BODY_BUFFER)

        # Handle default value, var args, kwargs
        self.write_def_args_default(f.args, is_method and not is_static)


        # Write self = this
        if is_method and not is_static:
            self.curr_scope.declare_variable(f.args.args[0].name)
            self.write("%s = this;"%f.args.args[0].name)

        # Function body
        if "JSNoOp" in decorators:
            self.write("return undefined;")
        else:
            self.write(self.exe_body(f.body, True, True))

        self.write("}")
        self.write_decorators(f)

        self.pop_context()


    def visit_tryexcept(self, tf):
        ex_var = self.curr_scope.generate_variable("_ex")

        self.write("try{ %s }" % self.exe_body(tf.body, True, True))
        self.write("catch (%s){" % ex_var)
        has_first = False
        has_catch_all = False
        for handler in tf.handlers:
            has_if = False
            if handler.type is not None:
                if has_first:
                    self.write("else ")
                if isinstance(handler.type, nodes.AssAttr) or isinstance(handler.type, nodes.Name):
                    self.write("if (%s instanceof %s){" %(ex_var, self.exe_node(handler.type)))
                elif isinstance(handler.type, nodes.Tuple):
                    self.write("if (%s){" % self.exe_first_differs(handler.type.elts,
                        rest_text="||",
                        do_visit=lambda elt: self.write("(%s instanceof %s)" % (ex_var, self.exe_node(elt)))
                    ))
                has_if = has_first = True
            else:
                has_catch_all = True
                if has_first:
                    self.write("else {")
                    has_if = True
                has_first = True
            if handler.name is not None:
                self.write("%s = %s;" %(handler.name.name, ex_var))
            self.write(self.exe_body(handler.body, True, True))
            if has_if:
                self.write("}");
        if not has_catch_all:
            if has_first:
                if self.use_throw_helper:
                    throw = self.get_util_var_name("_throw", "%s.helpers.throw" % self.LIB_NAME)
                    file = self.get_util_var_name("__py_file__", "'%s'" % self.input_name)
                    self.write("else { %s(%s, %s, %d); }"% (throw, ex_var, file, tf.lineno))
                else:
                    self.write("else { throw %s }" % ex_var)
        self.write("}");

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

        if isinstance(f.target, nodes.AssName):
            iter_var = f.target.name
        else:
            is_tuple = True
            iter_var = []
            for elt in f.target.elts:
                t = elt.name
                iter_var.append(t)

        self.push_context(lc.name)
        self.change_buffer(self.HEADER_BUFFER)
        self.write(" (function(){ ")
        self.change_buffer(self.BODY_BUFFER)

        i_var = self.curr_scope.generate_variable("_i")
        len_var = self.curr_scope.generate_variable("_len")
        results_var = self.curr_scope.generate_variable("_results")

        list_var = self.curr_scope.generate_variable("_list")
        iter_name = self.get_util_var_name("_iter", "%s.helpers.iter" % self.LIB_NAME);

        self.write("%s = []; " % results_var)
        self.write("%s = %s(%s); " % (list_var, iter_name, self.exe_node(f.iter)))
        self.write("for (%s = 0, %s = %s.length; %s < %s; %s++) {" % (i_var, len_var, list_var, i_var, len_var, i_var))
        if not is_tuple:
            self.write(    "%s = %s[%s];" % (iter_var, list_var, i_var))
        else:
            for i in range(0, len(iter_var)):
                self.write("%s = %s[%s][%d];" % (iter_var[i], list_var, i_var, i))
        for _if in f.ifs:
            self.write("    if (%s)" % self.exe_node(_if))
        self.write(            "%s.push(%s);" % (results_var, self.exe_node(lc.elt)))
        self.write("}")
        self.write("return %s;" % results_var)
        self.write("})()")

        self.pop_context()


    def visit_raise(self, r):
        exc = self.exe_node(r.exc)

        if self.use_throw_helper:
            throw = self.get_util_var_name("_throw", "%s.helpers.throw" %self.LIB_NAME)
            file = self.get_util_var_name("__py_file__", "'%s'" % self.input_name)
            self.write("%s(%s, %s, %d)"% (throw, exc, file, r.lineno))
        else:
            self.write("throw %s" % exc)

    def visit_print(self, p):
        """
        Translate print "aa" to print("aa")

        """
        self.write("print(%s)" % self.exe_first_differs(p.values, rest_text=","))

    def visit_discard(self, v):
        self.visit(v.value)

    def visit_const(self, t):
        if isinstance(t.value, str):
            self.write(simplejson.dumps(self.translator(t.value)))
        elif isinstance(t.value, bool):
            self.write(str(t.value).lower())
        elif isinstance(t.value, int) or isinstance(t.value, float):
            self.write(str(t.value))
        elif t.value is None:
            self.write("null")
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
            self.write_def_args(l.args)
        self.write("function(%s) {return %s; }" % (args.result, self.exe_node(l.body)))

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
            self.write("return %s" % self.exe_node(r.value))
        else:
            self.write("return")

    def visit_list(self, l):
        """
        Translate a list expression.

        """
        self.write("[%s]" % self.exe_first_differs(l.elts, rest_text=","))

    def visit_delete(self, d):
        """
        Translate a delete statement.

        """
        for target in d.targets:
            if isinstance(target, nodes.Subscript):
                self.visit(target)
            else:
                self.write("delete %s" % self.exe_node(target))


    def visit_pass(self, p):
        """
        Translate the `pass` statement. Places a comment.

        """
        self.write("/* pass */")

    def visit_continue(self, c):
        """
        Translate the `continue` statement.

        """
        self.write("continue")

    def visit_break(self, c):
        """
        Translate the `break` statement.

        """
        self.write("break")

    def visit_getattr(self, a):
        """
        Translate an attribute chain.

        """
        self.write("%s.%s" % (self.exe_node(a.expr), a.attrname))

    def visit_assattr(self, a):
        """
        Translate an attribute chain.

        """
        self.write("%s.%s" % (self.exe_node(a.expr), a.attrname))


    def visit_if(self, i):
        """
        Translate an if-block.

        """
        test = self.exe_node(i.test)
        if isinstance(i.test, nodes.Compare):
            self.write("".join(i.test.inits))
        self.write("if ( %s ) { %s }" % (test, self.exe_body(i.body)))
        if len(i.orelse) > 0:
            self.write("else {%s}" % self.exe_body(i.orelse))


    def visit_ifexp(self, i):
        """
        Translate an if-expression.

        """
        test = self.exe_node(i.test)
        if isinstance(i.test, nodes.Compare):
            if len(i.test.inits) > 0:
                self.raise_error("if else node cannot have complicated multiple comparison", i)
        self.write("%s ? %s : %s" % (test, self.exe_node(i.body), self.exe_node(i.orelse)))

    def visit_while(self, w):
        """
        Translate a while loop.

        """
        if len(w.orelse) > 0:
            self.raise_error("`else` branches of the `while` statement are not supported", w.orelse[0])

        test = self.exe_node(w.test)
        if isinstance(w.test, nodes.Compare):
            self.write("".join(w.test.inits))

        self.write("while (%s){ %s }" % (test, self.exe_body(w.body)))

    def visit_tryfinally(self, tf):
        self.write("try{ %s } finally { %s }" % (self.exe_body(tf.body, True, True),  self.exe_body(tf.finalbody, True, True)))

    def visit_assert(self, a):
        pass

    def visit_tuple(self, t):
        self.write("[%s]" % self.exe_first_differs(t.elts, rest_text=","))

