from logilab.astng.exceptions import InferenceError
import simplejson, re
import sys
import logging

from logilab.astng import nodes

from prambanan.compiler.translator import BaseTranslator
from prambanan.compiler.utils import ParseError, Writer

import utils
import inference

logger = logging.getLogger("prambanan")

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

        @translate-spec
            from module import itema, itemb
        ->
            var __builtin__, __import__, _m_module, itema, itemb;
            __builtin__ = prambanan.import('__builtin__');
            __import__ = __builtin__.__import__;
            _m_module = __import__('module'); itema = _m_module.itema;  itemb = _m_module.itemb;

        @translate-spec
            from module import itema
        ->
            var __builtin__, __import__, _m_module, itema;
            __builtin__ = prambanan.import('__builtin__');
            __import__ = __builtin__.__import__;
            _m_module = __import__('module'); itema = _m_module.itema;

        @translate-spec
            from module.submodule import itema
        ->
            var __builtin__, __import__, _m_module, itema;
            __builtin__ = prambanan.import('__builtin__');
            __import__ = __builtin__.__import__;
            _m_module = __import__('module').submodule; itema = _m_module.itema;

        @translate-spec
            from module.submodule.submodule2 import itema
        ->
            var __builtin__, __import__, _m_module, itema;
            __builtin__ = prambanan.import('__builtin__');
            __import__ = __builtin__.__import__;
            _m_module = __import__('module').submodule.submodule2; itema = _m_module.itema;
        """
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
                    m = i.root().import_module(module)
                    for l_name, locals in m.locals.items():
                        for l in locals:
                            if isinstance(l, nodes.Function) or isinstance(l, nodes.AssName) or isinstance(l, nodes.Class):
                                #todo hack
                                if self.modname == "prambanan"  and l_name in ["document", "window"]:
                                    continue
                                if not l_name.startswith("__") and l_name not in self.public_identifiers:
                                    self.public_identifiers.append(l_name)
                    if self.native is not None:
                        self.write("".join(self.native))
                    else:
                        logger.warn("native imported but native.js isn't provided in %s \n" % self.input_name)
                    return
                else:
                    self.raise_error("import * except native is not supported", i)
        modulevarname = module if "." not in module else module[0:module.find(".")]
        modulevarname = self.curr_scope.generate_variable("_m_"+modulevarname)
        if "." in module:
            splitted = module.split(".", 1)
            self.write("%s = __import__('%s').%s; " % (modulevarname, splitted[0], splitted[1]))
        else:
            self.write("%s = __import__('%s'); " % (modulevarname, module))
        for name,asname in i.names:
            varname = asname if asname else name
            if varname in utils.RESERVED_WORDS:
                if not varname in self.translated_names:
                    self.translated_names[varname] = self.mod_scope.generate_variable("__keyword_"+varname)
                varname = self.translated_names[varname]
            self.write("%s = %s.%s;  " % (varname, modulevarname, name))

    def visit_import(self, i):
        """
        @translate-spec
            import module
        ->
            var __builtin__, __import__, module;
            __builtin__ = prambanan.import('__builtin__');
            __import__ = __builtin__.__import__;
            module = __import__('module');

        @translate-spec
            import module.submodule
        ->
            var __builtin__, __import__, module;
            __builtin__ = prambanan.import('__builtin__');
            __import__ = __builtin__.__import__;
            module = __import__('module');

        @translate-spec
            import module.submodule as alias
        ->
            var __builtin__, __import__, alias;
            __builtin__ = prambanan.import('__builtin__');
            __import__ = __builtin__.__import__;
            alias = __import__('module').submodule;
        """
        first = True
        for name, asname in i.names:
            importname = name
            importattr = None
            varname = name
            if asname:
                varname = asname
                if "." in importname:
                    splitted = importname.split(".", 1)
                    importname = splitted[0]
                    importattr = splitted[1]
            else:
                if "." in importname:
                    importname = importname[0:importname.find(".")]
                    varname = importname
            if importattr is None:
                self.write("%s = __import__('%s');" % (varname, importname))
            else:
                self.write("%s = __import__('%s').%s;" % (varname, importname, importattr))


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

        if inference.infer_qname(c.func) == "prambanan.JS":
            if len(c.args) != 1:
                raise ParseError("native js only accept one argument", c.lineno, c.col_offset)
            if not isinstance(c.args[0], nodes.Const) and not isinstance(c.args[0].value, str):
                raise ParseError("native js only accept string",c.lineno, c.col_offset)
            self.write(re.sub(r'(?:@{{[!]?)([^}}]*)(?:}})', r"\1",c.args[0].value))
            return

        if isinstance(c.func, nodes.Name):
            call_type = "name"
        elif isinstance(c.func, nodes.Getattr):
            call_type = "getattr"
            if cls is not None and isinstance(c.func.expr, nodes.CallFunc) and isinstance(c.func.expr.func, nodes.Name) :
                if c.func.expr.func.name == "super":
                    # A super call
                    if (not len(c.func.expr.args) == 2):
                        self.raise_error("Only python 2 simple super supported", c)
                    attrname = c.func.attrname
                    self.write("%s(" % self.get_util_var_name("_super", "%s.helpers.super" % self.lib_name))
                    self.write("%s, this, '%s')" %  (self.exe_node(c.func.expr.args[0]), attrname))
                    method_written = True

        if type is None and "type" in self.warnings:
            logger.warn(" Warning: Cannot infer type [ call: %s, name: %s ] in line %s\n" % (call_type, name, c.lineno ))
        elif type == "Class":
            self.write("new ")

        if not method_written:
            self.walk(c.func)
        self.write("(")
        self.write_call_args(c)
        self.write(")")

    def visit_assname(self, n):
        if n.name in utils.RESERVED_WORDS:
            if not n.name in self.translated_names:
                self.translated_names[n.name] = self.mod_scope.generate_variable("__keyword_"+n.name)
            self.write(self.translated_names[n.name])
        else:
            self.write(n.name)

    def visit_delname(self, n):
        self.write("delete %s" % n.name)

    def visit_name(self, n):
        self.curr_scope.check_builtin_usage(n.name)
        self.visit_assname(n)

    def visit_binop(self, o):
        """
        Translates a binary operator.
        Note: The modulo operator on strings is translated to left.sprintf(right)
        and currently the only spot where tuples are allowed.

        """
        if o.op == "%" and not inference.is_instance(o.left, self.create("int"), self.create("float")):
            args = self.exe_first_differs(o.right.elts, rest_text=",") if isinstance(o.right, nodes.Tuple) else self.exe_node(o.right)
            self.write("(%s).__mod__(%s)" % (self.exe_node(o.left), args))
        elif o.op == "**":
            pow_helper = self.get_util_var_name("_pow", "%s.helpers.pow" % self.lib_name)
            self.write("%s(%s, %s)" % (pow_helper, self.exe_node(o.left), self.exe_node(o.right)))
        else:
            chars, prec, assoc = utils.get_op_cpa(o.op)
            self.walk(o.left)
            self.write(" %s " % (chars))
            eprec, eassoc = utils.get_expr_pa(o.right)
            if eprec >= prec: self.write("(")
            self.walk(o.right)
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
            self.walk(expr)
            if eprec >= prec: self.write(")")

    def visit_unaryop(self, o):
        """
        Translates a unary operator.

        """
        self.write(utils.get_op(o.op))
        prec, assoc = utils.get_expr_pa(o.operand)
        if isinstance(o.operand, nodes.Const): prec = 3
        if prec > 2: self.write("(")
        self.walk(o.operand)
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
                in_helper = self.get_util_var_name("_in", "%s.helpers.in"%self.lib_name)
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

        @translate-spec
            {'kutumbaba': 3}
        ->
            {kutumbaba: 3};

        @translate-spec
            {'0kutumbaba': 3}
        ->
            {"0kutumbaba": 3};


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
                self.walk(value)
        self.write("{%s}" % items.result)

    def visit_subscript(self, s):
        """
        Translate a subscript expression.

        """
        inferred_value = inference.infer_one(s.value)
        if isinstance(inferred_value, nodes.Dict) or inference.inferred_is_of_class(inferred_value, self.create("dict")):
            s.simple = True
            self.write('%s[%s]' % (self.exe_node(s.value), self.exe_node(s.slice.value)))
            if isinstance(s.parent, nodes.Delete):
                s.deleted = False
            return

        #   optimize simple index slice
        if not isinstance(s.parent, nodes.Delete):
            if isinstance(s.slice, nodes.Index):
                inferred_index = inference.infer_one(s.slice.value)
                if isinstance(inferred_value, nodes.List) or inference.inferred_is_of_class(inferred_value, self.create("list")):
                    if isinstance(inferred_index, nodes.Const) and inferred_index.value >= 0:
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

        subscript = self.get_util_var_name("_subscript", ("%s.helpers.subscript" % self.lib_name))
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
        @translate-spec
            a, b = c
        ->
            var a, b;(function(_source){a = _source[0]; b = _source[1]; })(c);

        @translate-spec
            c = a,b
        ->
            var c;c = [a,b];

        @translate-spec
           a = b = c
        ->
           var a, b;a = b = c;

        @translate-error
            d = a,b = x



        """
        is_target_tuple_exists = False
        tuple_target = None
        for target in a.targets:
            if isinstance(target, nodes.Tuple):
                is_target_tuple_exists = True
                tuple_target = target

        if is_target_tuple_exists and len(a.targets) > 1:
            self.raise_error("tuple are not allowed on multiple assignment", tuple_target)

        if is_target_tuple_exists:
            self.write("(function(_source){")
            tuple = a.targets[0]
            for i in range(0, len(target.elts)):
                elt = tuple.elts[i]
                self.walk(elt)
                self.write(" = _source[%d]; " % i)
            self.write("})(")
        else:
            for target in a.targets:
                self.walk(target)
                if isinstance(target, nodes.Subscript) and not target.simple:
                    self.write(", ")
                else:
                    self.write(" = ")

        if isinstance(a.value, nodes.Tuple):
            self.write("[%s]" % self.exe_first_differs(a.value.elts, rest_text=","))
        else:
            self.walk(a.value)

        if is_target_tuple_exists:
            self.write(")")
        if isinstance(target, nodes.Subscript) and not target.simple:
            self.write(")")

    def visit_augassign(self, a):
        """
        Translate an assignment operator.

        @tranlate-spec:
            a += 1
        ->
            a++;

        @translate-spec
            a += b
        ->
            a += b;


        """
        self.walk(a.target)
        if isinstance(a.value, nodes.Const) and a.value == 1:
            if isinstance(a.op, nodes.Add):
                self.write("++")
                return
            elif isinstance(a.op, nodes.Sub):
                self.write("--")
                return
        self.write(" %s= " % (utils.get_op(a.op[:-1])))
        self.walk(a.value)

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

        iter_type = inference.infer_one(f.iter)
        if isinstance(iter_type, nodes.List) or inference.inferred_is_of_class(iter_type, self.create("list")):
            iter_value = self.exe_node(f.iter)
        else:
            iter_name = self.get_util_var_name("_iter", "%s.helpers.iter" % self.lib_name);
            iter_value = "%s(%s)" % (iter_name, self.exe_node(f.iter))

        if not is_tuple:
            init = ("%s = %s[%s];" % (iter_var, list_var, i_var))
        else:
            for i in range(0, len(iter_var)):
                init = init + ("%s = %s[%s][%d];" % (iter_var[i], list_var, i_var, i))

        self.write("%s = %s;" % (list_var, iter_value))
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
        fullname = "t__%s_" % c.name if self.modname == "" else "t_%s_%s" % (self.modname.replace(".", "_"), c.name)
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
        create_class = self.get_util_var_name("_class", "%s.helpers.class" %self.lib_name)
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
                if not "staticmethod" in decorators and not "classmethod" in decorators:
                    proto_only.append(stmt.name)
                else:
                    cls_only.append(stmt.name)

            self.walk(stmt)
            self.write_semicolon(stmt);

        all_attrs = set(exported).difference(set(proto_only)).difference(set(cls_only))

        def write_attrs(attrs):
            content = self.exe_first_differs(attrs, rest_text = ",", do_visit = lambda(x): self.write("%s:%s" %(x, x)))
            self.write("{%s}"% content)

        content = self.exe_first_differs([proto_only, cls_only, all_attrs], rest_text = ",", do_visit = write_attrs)
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
        if "JS_noop" in decorators:
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
                if isinstance(handler.type, nodes.Getattr) or isinstance(handler.type, nodes.Name):
                    self.write("if (%s instanceof %s){" %(ex_var, self.exe_node(handler.type)))
                elif isinstance(handler.type, nodes.Tuple):
                    self.write("if (%s){" % self.exe_first_differs(handler.type.elts,
                        rest_text="||",
                        do_visit=lambda elt: self.write("(%s instanceof %s)" % (ex_var, self.exe_node(elt)))
                    ))
                else:
                    self.raise_error("handler type not recognized %s" % handler.type.__class__.name, handler.type)
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
                    throw = self.get_util_var_name("_throw", "%s.helpers.throw" % self.lib_name)
                    err = self.get_util_var_name("_err", "%s.Error" % self.lib_name)
                    file = self.get_util_var_name("__py_file__", "%s" % simplejson.dumps(self.input_path))
                    self.write("else { throw %s(%s, %s, %d, new %s()); }"% (throw, ex_var, file, tf.lineno, err))
                else:
                    self.write("else { throw %s }" % ex_var)
        self.write("}");

    def visit_listcomp(self, lc):
        """
        @translate-spec
           [i for i in l]
        ->
           (function(){
               var _i, _len, _list, _results;_results = [];
               _list = prambanan.helpers.iter(l);
                   for (_i = 0, _len = _list.length; _i < _len; _i++) {
                       i = _list[_i];
                       _results.push(i);
                   }
                   return _results;
           })();

        @translate-error
            [i for i in l for j in l2]
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
        self.write("(function(){ ")
        self.change_buffer(self.BODY_BUFFER)

        i_var = self.curr_scope.generate_variable("_i")
        len_var = self.curr_scope.generate_variable("_len")
        results_var = self.curr_scope.generate_variable("_results")

        list_var = self.curr_scope.generate_variable("_list")
        iter_name = self.get_util_var_name("_iter", "%s.helpers.iter" % self.lib_name);

        self.write("%s = []; " % results_var)
        self.write("%s = %s(%s); " % (list_var, iter_name, self.exe_node(f.iter)))
        self.write("for (%s = 0, %s = %s.length; %s < %s; %s++) { " % (i_var, len_var, list_var, i_var, len_var, i_var))
        if not is_tuple:
            self.write(    "%s = %s[%s];" % (iter_var, list_var, i_var))
        else:
            for i in range(0, len(iter_var)):
                self.write("%s = %s[%s][%d];" % (iter_var[i], list_var, i_var, i))
        for _if in f.ifs:
            self.write(    " if (%s)" % self.exe_node(_if))
        self.write(            " %s.push(%s);" % (results_var, self.exe_node(lc.elt)))
        self.write(" }")
        self.write(" return %s;" % results_var)
        self.write(" })()")

        self.pop_context()


    def visit_raise(self, r):
        """
        @translate-spec
            raise Exception()
        ->
            var Exception, __builtin__;
            __builtin__ = prambanan.import('__builtin__');
            Exception = __builtin__.Exception;
            prambanan.helpers.throw(new Exception(), 'source.py', 1);

        """
        exc = self.exe_node(r.exc)

        if self.use_throw_helper:
            throw = self.get_util_var_name("_throw", "%s.helpers.throw" %self.lib_name)
            err = self.get_util_var_name("_err", "%s.Error" % self.lib_name)
            file = self.get_util_var_name("__py_file__", "%s" % simplejson.dumps(self.input_path))
            self.write("throw %s(%s, %s, %d, new %s())"% (throw, exc, file, r.lineno, err))
        else:
            self.write("throw %s" % exc)

    def visit_print(self, p):
        """
        @translate-spec
            print "str"
        ->
            var __builtin__, print;
            __builtin__ = prambanan.import('__builtin__');
            print = __builtin__.print;
            print("str");

        """
        self.write("print(%s)" % self.exe_first_differs(p.values, rest_text=","))

    def visit_discard(self, v):
        self.walk(v.value)

    def visit_const(self, t):
        """

        @translate-spec
            "str".c()
        ->
            "str".c();

        @translate-spec
            True
        ->
            true;

        @translate-spec
            False
        ->
            false;

        @translate-spec
            None
        ->
            null;


        """
        if isinstance(t.value, basestring):
            self.write(simplejson.dumps(self.translator(t.value)))
        elif isinstance(t.value, bool):
            self.write(str(t.value).lower())
        elif isinstance(t.value, int) or isinstance(t.value, float):
            self.write(str(t.value))
        elif t.value is None:
            self.write("null")
        else:
            raise ValueError("const not recognized %s" )

    def visit_global(self, g):
        """
        Declares variables as global.

        """
        pass

    def visit_lambda(self, l):
        """
        Translates a lambda function.
        @translate-spec
            lambda x : x * 2
        ->
            function(x) { return x * 2; };

        """
        with self.Executor() as args:
            self.write_def_args(l.args)
        self.write("function(%s) { return %s; }" % (args.result, self.exe_node(l.body)))

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
                target.deleted = True
                subscript = self.exe_node(target)
                if target.deleted:
                    self.write(subscript)
                else:
                    self.write("delete %s" % subscript)
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

        @translate-spec
            if c:
                a()
        ->
            if (c) { a(); }

        @translate-spec
            if c:
                a()
            else:
                b()
        ->
            if (c) { a(); } else { b(); }
        """
        test = self.exe_node(i.test)
        if isinstance(i.test, nodes.Compare):
            self.write("".join(i.test.inits))
        self.write("if (%s) { %s }" % (test, self.exe_body(i.body)))
        if len(i.orelse) > 0:
            self.write(" else { %s }" % self.exe_body(i.orelse))


    def visit_ifexp(self, i):
        """
        Translate an if-expression.

        @translate-spec
            2 if c < 3 else 4
        ->
            c < 3 ? 2 : 4;

        @translate-spec
            2 if 1 < c < 3 else 4
        ->
            (1 < c)&&(c < 3) ? 2 : 4;

        @translate-error
            2 if 1 < call(c) < 3 else 4
        """
        test = self.exe_node(i.test)
        if isinstance(i.test, nodes.Compare):
            if len(i.test.inits) > 0:
                self.raise_error("if else node cannot have complicated multiple comparison", i)
        self.write("%s ? %s : %s" % (test, self.exe_node(i.body), self.exe_node(i.orelse)))

    def visit_while(self, w):
        """
        Translate a while loop.

        @translate-spec
            while c:
                c
        ->
            while (c) { c; }

        @translate-error
            while c:
                c
            else:
                c
        """
        if len(w.orelse) > 0:
            self.raise_error("`else` branches of the `while` statement are not supported", w.orelse[0])

        test = self.exe_node(w.test)
        if isinstance(w.test, nodes.Compare):
            self.write("".join(w.test.inits))

        self.write("while (%s) { %s }" % (test, self.exe_body(w.body)))

    def visit_tryfinally(self, tf):
        """
        @translate-spec
            try:
                c()
            finally:
                a()
        ->
            try { c(); } finally { a(); }

        """
        self.write("try { %s } finally { %s }" % (self.exe_body(tf.body, True, True),  self.exe_body(tf.finalbody, True, True)))

    def visit_assert(self, a):
        pass

    def visit_tuple(self, t):
        self.write("[%s]" % self.exe_first_differs(t.elts, rest_text=","))

