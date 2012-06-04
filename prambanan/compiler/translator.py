from collections import OrderedDict
from logilab.astng import nodes
from logilab.astng.exceptions import UnresolvableName, InferenceError
from logilab.astng.utils import ASTWalker

import gettext
from prambanan.compiler.utils import ParseError, Writer

import utils
import inference
from .scope import Scope

class BufferedWriter(object):
    HEADER_BUFFER = "header"
    BODY_BUFFER = "body"
    FOOTER_BUFFER = "footer"

    BUFFER_NAMES = [HEADER_BUFFER, BODY_BUFFER, FOOTER_BUFFER]

    def __init__(self, out, walk):
        self.writer_stack = []
        self.out = out
        self.curr_writer = Writer(self.BODY_BUFFER, self.BUFFER_NAMES)
        self.__walk = walk

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

    def write(self, s):
        self.curr_writer.write(s)

    def exe_node(self, node):
        with self.Executor() as exe:
            self.__walk(node)
        return exe.result

    def exe_body(self, body, skip_docstring=False, skip_global=False):
        with self.Executor() as exe:
            for stmt in body:
                """
                if skip_docstring and isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Str):
                    continue # Skip docstring
                """
                if skip_global and isinstance(stmt, nodes.Global): # The `global` statement is invisible
                    self.__walk(stmt)
                    continue
                self.__walk(stmt)
                self.write_semicolon(stmt)
        return exe.result

    def exe_first_differs(self, body, first_text=None, rest_text=None, do_visit=None):
        if do_visit is None:
            do_visit = lambda node: self.__walk(node)

        with self.Executor() as exe:
            first = True
            for node in body:
                if first:
                    first = False
                    if first_text is not None:
                        self.write(first_text)
                else:
                    if rest_text is not None:
                        self.write(rest_text)
                do_visit(node)

        return exe.result

    def change_buffer(self, buffer_name):
        self.curr_writer.change_buffer(buffer_name)

    def push_writer(self):
        self.writer_stack.append(self.curr_writer)
        old_writer = self.curr_writer
        self.curr_writer = Writer(self.BODY_BUFFER, self.BUFFER_NAMES)
        self.curr_writer.indent_level = old_writer.indent_level

    def pop_writer(self):
        old_writer = self.writer_stack.pop()
        old_writer.buffers[self.BODY_BUFFER].extend(self.curr_writer.buffers[self.HEADER_BUFFER])
        old_writer.buffers[self.BODY_BUFFER].extend(self.curr_writer.buffers[self.BODY_BUFFER])
        self.curr_writer = old_writer

    def flush_all_buffer(self):
        self.out.write("".join(self.curr_writer.buffers[self.HEADER_BUFFER]))
        self.out.write("".join(self.curr_writer.buffers[self.BODY_BUFFER]))
        self.curr_writer = Writer(self.BODY_BUFFER, self.BUFFER_NAMES)

class BaseTranslator(BufferedWriter, ASTWalker):
    def __init__(self, scope, direct_visitors, config):
        ASTWalker.__init__(self, self)
        BufferedWriter.__init__(self, config["output"], self.walk)
        self.mod_scope = scope
        self.curr_scope = None
        self.lib_name = scope.generate_variable("prambanan", False)

        self.input_lines = config["input_lines"]
        self.direct_visitors = direct_visitors

        self.input_name = config.get("input_name", "")
        self.modname = config.get("modname", "")
        self.warnings = config.get("warnings", {})
        self.bare = config.get("bare", False)
        self.translator = config.get("translator", gettext.NullTranslations().gettext)
        self.native = config.get("native", None)

        self.use_throw_helper = config.get("use_throw_helper", False)
        self.overridden_types = config.get("overridden_types", {})

        self.export_map = {}
        self.public_identifiers = []
        self.translated_names = {}
        self.util_names = {}

    def walk(self, node, _done=None):
        """walk on the tree from <node>, getting callbacks from handler"""
        if _done is None:
            _done = set()
        if node in _done:
            raise AssertionError((id(node), node, node.parent))
        _done.add(node)
        self.visit(node)
        self.leave(node)
        assert node.parent is not node

    def visit(self, node):
        kind = node.__class__.__name__.lower()

        if kind in self.direct_visitors:
            self.direct_visitors[kind](self, node)
            return

        visitors = OrderedDict()
        classes = [self.__class__]
        while len(classes) > 0:
            cls = classes.pop(0)
            for base in cls.__bases__:
                classes.append(base)
            visitor = getattr(cls, "visit_"+kind, None)
            if visitor is not None and cls not in visitors:
                visitors[cls] = visitor

        handled = False
        for cls, visitor in visitors.items():
            result = visitor(self, node)
            if result != False:
                handled = True
                break
        if not handled:
            raise ParseError("Could not parse node type '%s'" % str(node.__class__.__name__), node.lineno, node.col_offset)

    def infer_call_type(self, func):
        cls = self.curr_scope.class_context()
        if isinstance(func, nodes.Name):
            if self.curr_scope.check_builtin_usage(func.name):
                if func.name in Scope.BUILTINS_FUNC:
                    return "Function"
                else:
                    return "Class"
        elif isinstance(func, nodes.Getattr):
            if cls is not None and isinstance(func.expr, nodes.CallFunc) and isinstance(func.expr.func, nodes.Name) :
                if func.expr.func.name == "super":
                    return "Function"

        is_class = False
        is_func = False
        for inferred in inference.infer(func):
            qname = inferred.qname()
            if isinstance(qname, str):
                if qname.startswith("Module."):
                    qname = "%s.%s" % (self.modname, qname[len("Module."):])
                if qname in self.overridden_types:
                    return self.overridden_types[qname]
                if isinstance(inferred, nodes.Class):
                    is_class = True
                elif isinstance(inferred, nodes.Function):
                    is_func = True
        if is_class and is_func:
            return None
        if is_class:
            return "Class"
        if is_func:
            return "Function"
        return None

    def create(self, name):
        if ":" in name:
            module, attr = name.split(":")
        else:
            module = "__builtin__"
            attr = name

        root = self.mod_scope.node.root()
        result = root.import_module(module)
        for split in attr.split("."):
            result = result[split]

        return result

    def get_identifiers(self, stmt):
        names = []
        if isinstance(stmt, nodes.Class) or isinstance(stmt, nodes.Function):
            names.append(stmt.name)
        if isinstance(stmt, nodes.Assign):
            for target in stmt.targets:
                if isinstance(target, nodes.AssName):
                    names.append(target.name)
        return names

    def is_js_noop(self, dec):
        inferred = list(inference.infer(dec))
        if len(inferred) == 1:
            inferred_dec = inferred[0]
            if isinstance(inferred_dec, nodes.Function) and inferred_dec.decorators is not None:
                for dec_dec in inferred_dec.decorators.nodes:
                    if inference.infer_qname(dec_dec) == "prambanan.JS_noop_marker":
                        return True
        return False

    def is_static_method(self, dec):
        return inference.infer_qname(dec) == "__builtin__.staticmethod"

    def get_special_decorators(self, stmt):
        """
        Return a dictionary of decorators and their parameters.

        """
        decorators = {}
        if stmt.decorators is not None:
            for dec in stmt.decorators.nodes:
                if self.is_js_noop(dec):
                    decorators["JS_noop"] = True
                if isinstance(stmt, nodes.Function) and stmt.decorators is not None:
                    if self.is_static_method(dec):
                        decorators["staticmethod"] = True
        return decorators

    def push_context(self, identifier):
        """
        Walk context up.

        """
        old_context = self.curr_scope
        self.curr_scope = self.curr_scope.child(identifier)
        if self.curr_scope is None:
            raise ParseError("Lost context on accessing '%s' from '%s (%s)'" % (identifier, old_context.name, old_context.type))
        self.push_writer()

    def pop_context(self):
        """
        Walk context down.

        """
        self.change_buffer(self.HEADER_BUFFER)

        self.write_variables()
        self.curr_scope = self.curr_scope.parent
        self.pop_writer()

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

    def write_semicolon(self, stmt, no_newline = False):
        """
        Write a semicolon (and newline) for all statements except the ones
        in NO_SEMICOLON.

        """
        if stmt.__class__.__name__ not in utils.NO_SEMICOLON:
            self.write(";")

    def write_docstring(self, s):
        self.write("\n/**\n")
        gotnl = False
        first = True
        for line in s.split("\n"):
            line = line.strip()
            if line == "":
                gotnl = True
            else:
                if gotnl and not first:
                    self.write(" *")
                gotnl = False
                first = False
                self.write(" * %s\n" % (line))
        self.write(" */\n")

    def write_variables(self):
        if len(self.curr_scope.variables) > 0:
            first = True
            for variable in sorted(self.curr_scope.variables):
                if first:
                    self.write("var ")
                    first = False
                else:
                    self.write(", ")
                name = self.translated_names.get(variable, variable)
                self.write(name)
            self.write(";")


    def write_decorators(self, stmt):
        current = stmt.name
        if stmt.decorators is None:
            return

        for dec in stmt.decorators.nodes:
            if self.is_js_noop(dec) or self.is_static_method(dec):
                continue
            header = self.exe_node(dec)
            current = "%s(%s)" % (header, current)

        if stmt.name != current:
            self.write(";%s = %s" % (stmt.name, current))

    def write_call_args(self, args, comma_first=False):
        """
        Translate a list of arguments.

        """
        first = True
        i = 0
        for arg in args.args:
            if (not first) or comma_first:
                self.write(", ")
            first = False
            if isinstance(arg, nodes.Keyword):
                make_kwargs = self.get_util_var_name("_make_kwargs", "%s.helpers.make_kwargs" % self.lib_name)
                kwargs = self.exe_first_differs(args.args[i:], rest_text=",",do_visit=lambda arg: self.write("%s:%s" % (arg.arg, (self.exe_node(arg.value)))))
                self.write("%s({%s})" % (make_kwargs, kwargs))
                break
            else:
                self.walk(arg)
            i += 1

        if args.starargs is not None:
            if (not first) or comma_first:
                self.write(", ")
            first = False
            self.write(self.exe_node(args.starargs))

        if args.kwargs is not None:
            if (not first) or comma_first:
                self.write(", ")
            first = False
            self.write(self.exe_node(args.kwargs))

            """
        if len(args.keywords) > 0:
            #todo has keywords and kwargs
            if (not first) or comma_first:
                self.__write(", ")
            first = False
            """

    def write_def_args(self, args, strip_first = False):
        """
        Translate a list of arguments.

        """
        first = True
        for arg in args.args:
            if first:
                if strip_first and isinstance(arg, nodes.Name):
                    strip_first = False
                    continue
                first = False
            else:
                self.write(", ")
            self.walk(arg)

        if args.vararg is not None:
            if first:
                first = False
            else:
                self.write(", ")
            self.write(args.vararg)

        if args.kwarg is not None:
            if first:
                first = False
            else:
                self.write(", ")
            self.write(args.kwarg)

    def write_def_args_default(self, args, strip_first=False):
        """
        Translate the default arguments list.
        """
        if len(args.defaults) > 0 or args.vararg is not None or args.kwarg is not None:
            args_name = self.curr_scope.generate_variable("_args")
            init_args = self.get_util_var_name("_init_args", ("%s.helpers.init_args" % self.lib_name))
            self.write("%s = %s(arguments);" % (args_name , init_args))

        if len(args.defaults) > 0:
            first = len(args.args) - len(args.defaults)
            for i in xrange(len(args.defaults)):
                get_arg = self.get_util_var_name("_get_arg", ("%s.helpers.get_arg" % self.lib_name))
                arg_name = self.exe_node(args.args[first+i])
                index = first + i;
                if strip_first:
                    index -= 1
                self.write("%s = %s(%d, \"%s\", %s, %s);" % (arg_name, get_arg, index, arg_name, args_name, self.exe_node(args.defaults[i])))

        if args.vararg is not None:
            get_varargs = self.get_util_var_name("_get_varargs", ("%s.helpers.get_varargs" % self.lib_name))
            index = len(args.args)
            if strip_first:
                index -= 1
            self.write("%s = %s(%d, %s);" % (args.vararg, get_varargs, index, args_name))

        if args.kwarg is not None:
            get_kwargs = self.get_util_var_name("_get_kwargs", ("%s.helpers.get_kwargs" % self.lib_name))
            self.write("%s = %s(%s);" % (args.kwarg, get_kwargs, args_name))


