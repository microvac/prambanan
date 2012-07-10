import re
import sys
import itertools
import logging
import threading
import functools
import collections
import pickle
import textwrap

from chameleon.astutil import load
from chameleon.astutil import store
from chameleon.astutil import param
from chameleon.astutil import swap
from chameleon.astutil import subscript
from chameleon.astutil import node_annotations
from chameleon.astutil import annotated
from chameleon.astutil import NameLookupRewriteVisitor
from chameleon.astutil import Comment
from chameleon.astutil import Symbol
from chameleon.astutil import Builtin

from chameleon.codegen import TemplateCodeGenerator
from chameleon.codegen import template

from chameleon.tal import ErrorInfo
from chameleon.tal import NAME
from chameleon.i18n import fast_translate

from chameleon.nodes import Text
from chameleon.nodes import Value
from chameleon.nodes import Substitution
from chameleon.nodes import Assignment
from chameleon.nodes import Module
from chameleon.nodes import Context
from chameleon.nodes import Alias

from chameleon.tokenize import Token
from chameleon.config import DEBUG_MODE
from chameleon.exc import TranslationError
from chameleon.exc import ExpressionError
from chameleon.parser import groupdict

from chameleon.utils import DebuggingOutputStream
from chameleon.utils import char2entity
from chameleon.utils import ListDictProxy
from chameleon.utils import native_string
from chameleon.utils import byte_string
from chameleon.utils import string_type
from chameleon.utils import unicode_string
from chameleon.utils import version
from chameleon.utils import ast
from chameleon.utils import safe_native
from chameleon.utils import builtins
from chameleon.utils import decode_htmlentities
from prambanan.zpt import getitem, deleteitem, convert_str,escape, remove_el

convert_str.__module__ = "prambanan.zpt"
deleteitem.__module__ = "prambanan.zpt"
getitem.__module__ = "prambanan.zpt"
remove_el.__module__ = "prambanan.zpt"


if version >= (3, 0, 0):
    long = int

log = logging.getLogger('chameleon.compiler')

COMPILER_INTERNALS_OR_DISALLOWED = set([
    "econtext",
    "rcontext",
    "model_",
    "str",
    "int",
    "float",
    "long",
    "len",
    "None",
    "True",
    "False",
    "RuntimeError",
    ])

HTML_VOID_ELEMENTS = set([
    "area",
    "base",
    "br",
    "col",
    "command",
    "embed",
    "hr",
    "img",
    "input",
    "keygen",
    "link",
    "meta",
    "param",
    "source",
    "track",
    "wbr",
])
comment_re = re.compile("<!--.*?-->", re.DOTALL)


RE_MANGLE = re.compile('[^\w_]')
RE_NAME = re.compile('^%s$' % NAME)

if DEBUG_MODE:
    LIST = template("cls()", cls=DebuggingOutputStream, mode="eval")
else:
    LIST = template("[]", mode="eval")


def identifier(prefix, suffix=None):
    return "__%s_%s" % (prefix, mangle(suffix or id(prefix)))


def mangle(string):
    return RE_MANGLE.sub('_', str(string)).replace('\n', '')


def load_econtext(name):
    return template("econtext[KEY]", KEY=ast.Str(s=name), mode="eval")


def store_econtext(name):
    name = native_string(name)
    return subscript(name, load("econtext"), ast.Store())


def store_rcontext(name):
    name = native_string(name)
    return subscript(name, load("rcontext"), ast.Store())

def wrap_model_change(node, model, bind_ons, base_on_change, create_last_on_change):

    def get_names(prefix, i):
        if i != -1:
            name = "_".join(bind_ons[0:i+1])
            current = identifier("%s_%s"% (prefix, name), id(node))
        else:
            current = model

        if i > 0:
            name = "_".join(bind_ons[0:i])
            next = identifier("%s_%s" % (prefix, name), id(node))
        elif i == 0:
            next = model
        else:
            next = None
        return current, next
    def glbl(name):
        return ast.Global([ast.Name(id=name, ctx=ast.Load())])

    body = []
    body += base_on_change
    current_model, next_model = get_names("m", len(bind_ons) -1)
    body += template("MODEL=None", MODEL=current_model)

    on_change_name = identifier("on_change_%s" % ("_".join(bind_ons[0:len(bind_ons)])), id(node))

    last_on_change=create_last_on_change(current_model, next_model, bind_ons[-1])
    last_on_change = [glbl(current_model)] +last_on_change


    on_change_func = [ast.FunctionDef(
        name=on_change_name, args=ast.arguments(
            args=[],
            defaults=(),
        ),
        body=last_on_change
        )
    ]
    body+= on_change_func

    for i in range(len(bind_ons) - 2, -1, -1):
        bind_on = bind_ons[i]
        current_model, next_model = get_names("m", i)
        body += template("MODEL=None", MODEL=current_model)

        func_body = []
        func_body += [glbl(current_model)]
        func_body += emit_model_change(current_model, next_model, ast.Str(s="change:%s"%bind_ons[i-1]), ast.Str(s=bind_on), on_change_name)

        on_change_name = identifier("on_change_%s" % "_".join(bind_ons[0:i+1]), id(node))

        on_change_func = [ast.FunctionDef(
            name=on_change_name, args=ast.arguments(
                args=[],
                defaults=(),
            ),
            body=func_body
            )
        ]
        body += on_change_func

    body += template("MODEL.on(CHANGE_NAME, ON_CHANGE)", MODEL = model, CHANGE_NAME=ast.Str("change:%s"%bind_ons[0]), ON_CHANGE=on_change_name)
    body += template("ON_CHANGE()", ON_CHANGE=on_change_name)


    return body


def set_error(token, exception):
    try:
        line, column = token.location
        filename = token.filename
    except AttributeError:
        line, column = 0, 0
        filename = "<string>"

    string = safe_native(token)

    return template(
        "rcontext.setdefault('__error__', [])."
        "append((string, line, col, src, exc))",
        string=ast.Str(s=string),
        line=ast.Num(n=line),
        col=ast.Num(n=column),
        src=ast.Str(s=filename),
        sys=Symbol(sys),
        exc=exception,
        )


#ejos changed
def try_except_wrap(stmts, token):
    for stmt in stmts:
        yield stmt

@template
def emit_model_change(current_model, next_model, event_name, bind_on, on_change):
    if current_model:
        current_model.off(event_name, on_change)
    if next_model:
        current_model = next_model.get(bind_on)
    if current_model:
        current_model.on(event_name, on_change)
    on_change()


@template
def emit_node(node, STACK=None):  # pragma: no cover
    STACK.t(node)


#ejos
@template
def emit_node_if_non_trivial(node, STACK=None):  # pragma: no cover
    STACK.t(node)


@template
def emit_bool(target, s, default_marker=None,
                 default=None):  # pragma: no cover
    if target is default_marker:
        target = default
    elif target:
        target = s
    else:
        target = None


@template
def emit_convert(
    target, encoded=byte_string, str=unicode_string,
    long=long, type=type,
    default_marker=None, default=None):  # pragma: no cover
    if target is None:
        pass
    elif target is default_marker:
        target = default
    else:
        target = str(target)


@template
def emit_translate(target, msgid, default=None):  # pragma: no cover
    target = translate(msgid, default=default, domain=__i18n_domain)

@template
def emit_convert_structure(target, STACK=None):
    STACK.u(target)
    STACK.o()

@template
def emit_convert_and_escape(
    target, quote=None, quote_entity=None, str=unicode_string, long=long,
    type=type, encoded=byte_string,
    default_marker=None, default=None):  # pragma: no cover
    target = escape(target)


class Interpolator(object):
    braces_required_regex = re.compile(
        r'(?<!\\)\$({(?P<expression>.*)})',
        re.DOTALL)

    braces_optional_regex = re.compile(
        r'(?<!\\)\$({(?P<expression>.*)}|(?P<variable>[A-Za-z][A-Za-z0-9_]*))',
        re.DOTALL)

    def __init__(self, expression, braces_required, translate=False):
        self.expression = expression
        self.regex = self.braces_required_regex if braces_required else \
                     self.braces_optional_regex
        self.translate = translate

    def __call__(self, name, engine):
        """The strategy is to find possible expression strings and
        call the ``validate`` function of the parser to validate.

        For every possible starting point, the longest possible
        expression is tried first, then the second longest and so
        forth.

        Example 1:

          ${'expressions use the ${<expression>} format'}

        The entire expression is attempted first and it is also the
        only one that validates.

        Example 2:

          ${'Hello'} ${'world!'}

        Validation of the longest possible expression (the entire
        string) will fail, while the second round of attempts,
        ``${'Hello'}`` and ``${'world!'}`` respectively, validate.

        """

        body = []
        nodes = []
        text = self.expression

        expr_map = {}
        translate = self.translate

        while text:
            matched = text
            m = self.regex.search(matched)
            if m is None:
                nodes.append(ast.Str(s=text))
                break

            part = text[:m.start()]
            text = text[m.start():]

            if part:
                node = ast.Str(s=part)
                nodes.append(node)

            if not body:
                target = name
            else:
                target = store("%s_%d" % (name.id, text.pos))

            while True:
                d = groupdict(m, matched)
                string = d["expression"] or d["variable"] or ""

                string = decode_htmlentities(string)

                try:
                    compiler = engine.parse(string)
                    body += compiler.assign_text(target)
                except ExpressionError:
                    matched = matched[m.start():m.end() - 1]
                    m = self.regex.search(matched)
                    if m is None:
                        raise
                else:
                    break

            # If one or more expressions are not simple names, we
            # disable translation.
            if RE_NAME.match(string) is None:
                translate = False

            # if this is the first expression, use the provided
            # assignment name; otherwise, generate one (here based
            # on the string position)
            node = load(target.id)
            nodes.append(node)

            expr_map[node] = safe_native(string)

            text = text[len(m.group()):]

        if len(nodes) == 1:
            target = nodes[0]

            if translate and isinstance(target, ast.Str):
                target = template(
                    "translate(msgid, domain=__i18n_domain)",
                    msgid=target, mode="eval",
                    )
        else:
            if translate:
                formatting_string = ""
                keys = []
                values = []

                for node in nodes:
                    if isinstance(node, ast.Str):
                        formatting_string += node.s
                    else:
                        string = expr_map[node]
                        formatting_string += "${%s}" % string
                        keys.append(ast.Str(s=string))
                        values.append(node)

                target = template(
                    "translate(msgid, mapping=mapping, domain=__i18n_domain)",
                    msgid=ast.Str(s=formatting_string),
                    mapping=ast.Dict(keys=keys, values=values),
                    mode="eval"
                    )
            else:
                nodes = [
                    template(
                        "NODE",
                        NODE=node, mode="eval"
                        )
                    for node in nodes
                    ]

                target = ast.BinOp(
                    left=ast.Str(s="%s" * len(nodes)),
                    op=ast.Mod(),
                    right=ast.Tuple(elts=nodes, ctx=ast.Load()))
            body += [ast.Assign(targets=[name], value=target)]

        return body


class ExpressionEngine(object):
    """Expression engine.

    This test demonstrates how to configure and invoke the engine.

    >>> from chameleon import tales
    >>> parser = tales.ExpressionParser({
    ...     'python': tales.PythonExpr,
    ...     'not': tales.NotExpr,
    ...     'exists': tales.ExistsExpr,
    ...     'string': tales.StringExpr,
    ...     }, 'python')

    >>> engine = ExpressionEngine(parser)

    An expression evaluation function:

    >>> eval = lambda expression: tales.test(
    ...     tales.IdentityExpr(expression), engine)

    We have provided 'python' as the default expression type. This
    means that when no prefix is given, the expression is evaluated as
    a Python expression:

    >>> eval('not False')
    True

    Note that the ``type`` prefixes bind left. If ``not`` and
    ``exits`` are two expression type prefixes, consider the
    following::

    >>> eval('not: exists: int(None)')
    True

    The pipe operator binds right. In the following example, but
    arguments are evaluated against ``not: exists: ``.

    >>> eval('not: exists: help')
    False

    >>> eval('string:test ${1}${2}')
    'test 12'

    """

    supported_char_escape_set = set(('&', '<', '>'))

    def __init__(self, parser, char_escape=(),
                 default=None, default_marker=None):
        self._parser = parser
        self._char_escape = char_escape
        self._default = default
        self._default_marker = default_marker

    def __call__(self, string, target):
        # BBB: This method is deprecated. Instead, a call should first
        # be made to ``parse`` and then one of the assignment methods
        # ("value" or "text").

        compiler = self.parse(string)
        return compiler(string, target)

    def parse(self, string):
        expression = self._parser(string)
        compiler = self.get_compiler(expression, string)
        return ExpressionCompiler(compiler, self)

    def get_compiler(self, expression, string):
        def compiler(target, engine, result_type=None, *args):
            stmts = expression(target, engine)

            if result_type is not None:
                method = getattr(self, '_convert_%s' % result_type)
                if result_type == "text" and len(stmts) == 1 and isinstance(stmts[0], ast.Assign):
                    stmts = self._convert_text(target, stmts[0].value)
                else:
                    steps = method(target, *args)
                    stmts.extend(steps)
            return list(try_except_wrap(stmts, string))

        return compiler

    def _convert_bool(self, target, s):
        """Converts value given by ``target`` to a string ``s`` if the
        target is a true value, otherwise ``None``.
        """

        return emit_bool(
            target, ast.Str(s=s),
            default=self._default,
            default_marker=self._default_marker
            )

    def _convert_text(self, target, body=None):
        """Converts value given by ``target`` to text."""

        if self._char_escape:
            # This is a cop-out - we really only support a very select
            # set of escape characters
            other = set(self._char_escape) - self.supported_char_escape_set

            if other:
                for supported in '"', '\'', '':
                    if supported in self._char_escape:
                        quote = supported
                        break
                else:
                    raise RuntimeError(
                        "Unsupported escape set: %s." % repr(self._char_escape)
                        )
            else:
                quote = '\0'

            entity = char2entity(quote or '\0')

            if body is None:
                return emit_convert_and_escape(
                    target,
                    quote=ast.Str(s=quote),
                    quote_entity=ast.Str(s=entity),
                    default=self._default,
                    default_marker=self._default_marker,
                    )
            else:
                return template("T = convert(F)", F=body, T=target, convert=Symbol(convert_str))

        return emit_convert(
            target,
            default=self._default,
            default_marker=self._default_marker,
            )


class ExpressionCompiler(object):
    def __init__(self, compiler, engine):
        self.compiler = compiler
        self.engine = engine

    def assign_bool(self, target, s):
        return self.compiler(target, self.engine, "bool", s)

    def assign_text(self, target):
        return self.compiler(target, self.engine, "text")

    def assign_value(self, target):
        return self.compiler(target, self.engine)


class ExpressionEvaluator(object):
    """Evaluates dynamic expression.

    This is not particularly efficient, but supported for legacy
    applications.

    >>> from chameleon import tales
    >>> parser = tales.ExpressionParser({'python': tales.PythonExpr}, 'python')
    >>> engine = functools.partial(ExpressionEngine, parser)

    >>> evaluate = ExpressionEvaluator(engine, {
    ...     'foo': 'bar',
    ...     })

    The evaluation function is passed the local and remote context,
    the expression type and finally the expression.

    >>> evaluate({'boo': 'baz'}, {}, 'python', 'foo + boo')
    'barbaz'

    The cache is now primed:

    >>> evaluate({'boo': 'baz'}, {}, 'python', 'foo + boo')
    'barbaz'

    Note that the call method supports currying of the expression
    argument:

    >>> python = evaluate({'boo': 'baz'}, {}, 'python')
    >>> python('foo + boo')
    'barbaz'

    """

    __slots__ = "_engine", "_cache", "_names", "_builtins"

    def __init__(self, engine, builtins):
        self._engine = engine
        self._names, self._builtins = zip(*builtins.items())
        self._cache = {}

    def __call__(self, econtext, rcontext, expression_type, string=None):
        if string is None:
            return functools.partial(
                self.__call__, econtext, rcontext, expression_type
                )

        expression = "%s:%s" % (expression_type, string)

        try:
            evaluate = self._cache[expression]
        except KeyError:
            assignment = Assignment(["_result"], expression, True)
            module = Module("evaluate", Context(assignment))

            compiler = Compiler(
                self._engine, module, ('econtext', 'rcontext') + self._names
                )

            env = {}
            exec(compiler.code, env)
            evaluate = self._cache[expression] = env["evaluate"]

        evaluate(econtext, rcontext, *self._builtins)
        return econtext['_result']


class NameTransform(object):
    """
    >>> nt = NameTransform(
    ...     set(('foo', 'bar', )), {'boo': 'boz'},
    ...     ('econtext', ),
    ... )

    >>> def test(node):
    ...     rewritten = nt(node)
    ...     module = ast.Module([ast.fix_missing_locations(rewritten)])
    ...     codegen = TemplateCodeGenerator(module)
    ...     return codegen.code

    Any odd name:

    >>> test(load('frobnitz'))
    "getitem('frobnitz')"

    A 'builtin' name will first be looked up via ``get`` allowing fall
    back to the global builtin value:

    >>> test(load('foo'))
    "get('foo', foo)"

    Internal names (with two leading underscores) are left alone:

    >>> test(load('__internal'))
    '__internal'

    Compiler internals or disallowed names:

    >>> test(load('econtext'))
    'econtext'

    Aliased names:

    >>> test(load('boo'))
    'boz'

    """

    def __init__(self, builtins, aliases, internals, defined_models, get_current_el):
        self.builtins = builtins
        self.aliases = aliases
        self.internals = internals
        self.defined_models = defined_models
        self.get_current_el = get_current_el

    def __call__(self, node):
        name = node.id

        # Don't rewrite names that begin with an underscore; they are
        # internal and can be assumed to be locally defined. This
        # policy really should be part of the template program, not
        # defined here in the compiler.

        if isinstance(node.ctx, ast.Load):
            if name.startswith("__model_"):
                name = node.id[8:]
                if not name in self.defined_models:
                    raise TranslationError(
                        "Cannot find model.", name)
                node.id = self.defined_models[name]
                return node

        if name.startswith('__') or name in self.internals:
            return node

        if name == "el":
            return self.get_current_el()

        if isinstance(node.ctx, ast.Store):
            return store_econtext(name)

        aliased = self.aliases.get(name)
        if aliased is not None:
            return load(aliased)

        # If the name is a Python global, first try acquiring it from
        # the dynamic context, then fall back to the global.
        if name in self.builtins:
            return template(
                "getitem(econtext, key, name)",
                getitem=Symbol(getitem),
                mode="eval",
                key=ast.Str(s=name),
                name=load(name),
                )

        # Otherwise, simply acquire it from the dynamic context.
        return load_econtext(name)


class ExpressionTransform(object):
    """Internal wrapper to transform expression nodes into assignment
    statements.

    The node input may use the provided expression engine, but other
    expression node types are supported such as ``Builtin`` which
    simply resolves a built-in name.

    Used internally be the compiler.
    """

    loads_symbol = Symbol(pickle.loads)

    def __init__(self, engine_factory, cache, visitor, strict=True):
        self.engine_factory = engine_factory
        self.cache = cache
        self.strict = strict
        self.visitor = visitor

    def __call__(self, expression, target):
        if isinstance(target, string_type):
            target = store(target)

        try:
            stmts = self.translate(expression, target)
        except ExpressionError:
            if self.strict:
                raise

            exc = sys.exc_info()[1]
            p = pickle.dumps(exc)

            stmts = template(
                "__exc = loads(p)", loads=self.loads_symbol, p=ast.Str(s=p)
                )

            token = Token(exc.token, exc.offset, filename=exc.filename)

            stmts += set_error(token, load("__exc"))
            stmts += [ast.Raise(exc=load("__exc"))]

        # Apply visitor to each statement
        for stmt in stmts:
            self.visitor(stmt)

        return stmts

    def translate(self, expression, target):
        if isinstance(target, string_type):
            target = store(target)

        cached = self.cache.get(expression)

        if cached is not None:
            stmts = [ast.Assign(targets=[target], value=cached)]
        elif isinstance(expression, ast.expr):
            stmts = [ast.Assign(targets=[target], value=expression)]
        else:
            # The engine interface supports simple strings, which
            # default to expression nodes
            if isinstance(expression, string_type):
                expression = Value(expression, True)

            kind = type(expression).__name__
            visitor = getattr(self, "visit_%s" % kind)
            stmts = visitor(expression, target)

            # Add comment
            target_id = getattr(target, "id", target)
            comment = Comment(" %r -> %s" % (expression, target_id))
            stmts.insert(0, comment)

        return stmts

    def visit_Value(self, node, target):
        engine = self.engine_factory()
        compiler = engine.parse(node.value)
        return compiler.assign_value(target)

    def visit_Default(self, node, target):
        value = annotated(node.marker)
        return [ast.Assign(targets=[target], value=value)]

    def visit_Substitution(self, node, target):
        engine = self.engine_factory(
            char_escape=node.char_escape,
            default=node.default,
            )
        compiler = engine.parse(node.value)
        return compiler.assign_text(target)

    def visit_Negate(self, node, target):
        return self.translate(node.value, target) + \
               template("TARGET = not TARGET", TARGET=target)

    def visit_Identity(self, node, target):
        expression = self.translate(node.expression, "__expression")
        value = self.translate(node.value, "__value")

        return expression + value + \
               template("TARGET = __expression is __value", TARGET=target)

    def visit_Equality(self, node, target):
        expression = self.translate(node.expression, "__expression")
        value = self.translate(node.value, "__value")

        return expression + value + \
               template("TARGET = __expression == __value", TARGET=target)

    def visit_Boolean(self, node, target):
        engine = self.engine_factory()
        compiler = engine.parse(node.value)
        return compiler.assign_bool(target, node.s)

    def visit_Interpolation(self, node, target):
        expr = node.value
        if isinstance(expr, Substitution):
            engine = self.engine_factory(
                char_escape=expr.char_escape,
                default=expr.default,
                )
        elif isinstance(expr, Value):
            engine = self.engine_factory()
        else:
            raise RuntimeError("Bad value: %r." % node.value)

        interpolator = Interpolator(
            expr.value, node.braces_required, node.translation
            )

        compiler = engine.get_compiler(interpolator, expr.value)
        return compiler(target, engine)

    def visit_Translate(self, node, target):
        if node.msgid is not None:
            msgid = ast.Str(s=node.msgid)
        else:
            msgid = target
        return self.translate(node.node, target) + \
               emit_translate(target, msgid, default=target)

    def visit_Static(self, node, target):
        value = annotated(node)
        return [ast.Assign(targets=[target], value=value)]

    def visit_Builtin(self, node, target):
        value = annotated(node)
        return [ast.Assign(targets=[target], value=value)]


class Compiler(object):
    """Generic compiler class.

    Iterates through nodes and yields Python statements which form a
    template program.
    """

    exceptions = NameError, \
                 ValueError, \
                 AttributeError, \
                 LookupError, \
                 TypeError

    defaults = {
        }

    lock = threading.Lock()

    global_builtins = set(builtins.__dict__)

    def __init__(self, engine_factory, node, builtins={}, strict=True):
        self._scopes = [set()]
        self._expression_cache = {}
        self._translations = []
        self._builtins = builtins
        self._aliases = [{}]
        self._macros = []
        self._current_slot = []
        self._defined_models = {}
        self._current_stack = None

        internals = COMPILER_INTERNALS_OR_DISALLOWED | \
                    set(self.defaults)

        transform = NameTransform(
            self.global_builtins | set(builtins),
            ListDictProxy(self._aliases),
            internals,
            self._defined_models,
            self.get_current_el,
            )

        self._visitor = visitor = NameLookupRewriteVisitor(transform)

        self._engine = ExpressionTransform(
            engine_factory,
            self._expression_cache,
            visitor,
            strict=strict,
            )

        if isinstance(node_annotations, dict):
            self.lock.acquire()
            backup = node_annotations.copy()
        else:
            backup = None

        try:
            module = ast.Module([])
            module.body += self.visit(node)
            ast.fix_missing_locations(module)
            generator = TemplateCodeGenerator(module)
        finally:
            if backup is not None:
                node_annotations.clear()
                node_annotations.update(backup)
                self.lock.release()

        self.code = generator.code

    def get_current_el(self):
        return template("STACK.current", STACK=self._current_stack)[0]

    def visit(self, node):
        if node is None:
            return ()
        kind = type(node).__name__
        visitor = getattr(self, "visit_%s" % kind)
        iterator = visitor(node)
        res = list(iterator)
        return res

    def visit_Sequence(self, node):
        for item in node.items:
            for stmt in self.visit(item):
                yield stmt

    def visit_BindChange(self, node):
        body = []

        body.append(Comment("start model-binding"))

        new_stack = identifier("stack", id(node))
        old_stack = self._current_stack
        body += template("CAPTURED_STACK = STACK.capture()", CAPTURED_STACK=new_stack, STACK=old_stack)

        self._current_stack = new_stack
        self._aliases.append(self._aliases[-1].copy())

        inner = self.visit(node.node)

        self._aliases.pop()
        self._current_stack = old_stack

        on_change_name = identifier("on_change", id(node))
        on_change_func = [ast.FunctionDef(
            name=on_change_name, args=ast.arguments(
                args=[],
                defaults=(),
            ),
            body=inner
        )]
        if node.model_name not in self._defined_models:
            raise TranslationError(
                "Cannot find bind model on current context.", node.model_name)

        def create_last_on_change(model, next_model, attr):
            result = []

            sub = []
            if len(node.bind_attrs):
                for attr in node.bind_attrs:
                    sub += template("MODEL.off('change:%s', ON_CHANGE)" % attr, ON_CHANGE=on_change_name, MODEL=model)
            else:
                sub += template("MODEL.off('change', ON_CHANGE)", ON_CHANGE=on_change_name, MODEL=model)
            result += [ast.If(test=load(model), body=sub)]

            sub = []
            sub += template("MODEL = NEXT_MODEL.get(ATTR)", MODEL = model, NEXT_MODEL=next_model, ATTR=ast.Str(s=attr))
            result += [ast.If(test=load(next_model), body=sub)]

            sub = []
            if len(node.bind_attrs):
                for attr in node.bind_attrs:
                    sub += template("MODEL.on('change:%s', ON_CHANGE)" % attr, ON_CHANGE=on_change_name, MODEL=model)
            else:
                sub += template("MODEL.on('change', ON_CHANGE)", ON_CHANGE=on_change_name, MODEL=model)
            result += [ast.If(test=load(model), body=sub)]

            return result


        if node.bind_ons:
            body += wrap_model_change(node, self._defined_models[node.model_name], node.bind_ons, on_change_func, create_last_on_change)
        else:
            body += on_change_func
            model = self._defined_models[node.model_name]
            if len(node.bind_attrs):
                for attr in node.bind_attrs:
                    body += template("MODEL.on('change:%s', ON_CHANGE)" % attr, ON_CHANGE=on_change_name, MODEL=model)
            else:
                body += template("MODEL.on('change', ON_CHANGE)", ON_CHANGE=on_change_name, MODEL=model)
            body += template("ON_CHANGE()", ON_CHANGE=on_change_name)


        body.append(Comment("end model-binding"))
        return body

    def visit_BindRepeat(self, node):
        body = []

        body.append(Comment("start model-repeat-binding"))

        new_stack = identifier("stack", id(node))
        old_stack = self._current_stack
        body += template("CAPTURED_STACK = STACK.capture_for_repeat()", CAPTURED_STACK=new_stack, STACK=old_stack)

        el_map = identifier("el_map", id(node))
        body += template("EL_MAP = {}", EL_MAP=el_map)

        new_stack = identifier("stack", id(node))

        self._current_stack = new_stack
        self._aliases.append(self._aliases[-1].copy())

        model_name = identifier("model_%s" % node.alias, id(node))
        self._defined_models[node.alias] = model_name

        inner_on_add = []
        inner_on_add += self.visit(node.node)
        inner_on_add += template("EL_MAP[MODEL.cid] = STACK.repeat_el", EL_MAP=el_map, STACK=self._current_stack, MODEL=model_name)

        on_add_name = identifier("on_add", id(node))
        on_add_func = [ast.FunctionDef(
            name=on_add_name, args=ast.arguments(
                args=[load(model_name)],
                defaults=(),
            ),
            body=inner_on_add
        )]
        body += on_add_func

        inner_on_remove = []
        inner_on_remove += template("REMOVE_EL(EL_MAP[MODEL.cid])", REMOVE_EL=Symbol(remove_el), EL_MAP=el_map, MODEL=model_name)
        inner_on_remove += template("del EL_MAP[MODEL.cid]", EL_MAP=el_map, MODEL=model_name)
        on_remove_name = identifier("on_remove", id(node))
        on_remove_func = [ast.FunctionDef(
            name=on_remove_name, args=ast.arguments(
                args=[load(model_name)],
                defaults=(),
            ),
            body=inner_on_remove
        )]
        body += on_remove_func

        inner_on_reset = [ast.Global([load(el_map)])]
        inner_on_reset += [ast.For(
            target=store("cid"),
            iter=load(el_map),
            body = template("REMOVE_EL(EL_MAP[cid])", REMOVE_EL=Symbol(remove_el), EL_MAP=el_map)
        )]
        inner_on_reset += template("EL_MAP = {}" , EL_MAP=el_map)
        inner_on_reset.append(
            ast.If(
                test=load("models"),
                body=[ast.For(
                    target=store("model"),
                    iter=load("models"),
                    body=template("ON_ADD(model)", ON_ADD=on_add_name))
                ]))
        on_reset_name = identifier("on_reset", id(node))
        on_reset_func = [ast.FunctionDef(
            name=on_reset_name, args=ast.arguments(
                args=[load("models")],
                defaults=(),
            ),
            body=inner_on_reset
        )]
        body += on_reset_func

        collection = "__collection"
        initializer = self._engine(node.expression, store(collection))
        initializer += [ast.For(
            target=store("model"),
            iter=load(collection),
            body=template("ON_ADD(model)", ON_ADD=on_add_name)
        )]
        initializer += template("COLLECTION.on('add', ON_ADD)", COLLECTION=collection, ON_ADD=on_add_name)
        initializer += template("COLLECTION.on('remove', ON_REMOVE)", COLLECTION=collection, ON_REMOVE=on_remove_name)
        initializer += template("COLLECTION.on('reset', ON_RESET)", COLLECTION=collection, ON_RESET=on_reset_name)
        body += initializer

        self._aliases.pop()
        self._current_stack = old_stack

        body.append(Comment("end model-repeat-binding"))
        return body

    def visit_DefineModel(self, node):
        name = identifier("model_%s" % node.alias, id(node))
        self._defined_models[node.alias] = name
        body = self._engine(node.expression, store(name))
        body += self.visit(node.node)
        return body


    def visit_Element(self, node):
        self._aliases.append(self._aliases[-1].copy())

        for stmt in self.visit(node.start):
            yield stmt

        for stmt in self.visit(node.content):
            yield stmt

        for stmt in template("STACK.o()", STACK=self._current_stack):
            yield stmt

        self._aliases.pop()

    def visit_Module(self, node):
        body = []

        body += template("__marker = object()")
        body += self.visit(node.program)

        return body

    def visit_BindingProgram(self, node):
        functions = []

        self._current_stack = identifier("stack", id(node))
        self._defined_models[""] = identifier("model", id(node))

        # Visit defined macros
        macros = getattr(node, "macros", ())
        names = []
        for macro in macros:
            stmts = self.visit(macro)
            function = stmts[-1]
            names.append(function.name)
            functions += stmts


        return functions

    def visit_Context(self, node):
        return self.visit(node.node)


    def visit_Macro(self, node):
        body = []

        # Resolve defaults
        for name in self.defaults:
            body += template(
                "NAME = econtext[KEY]",
                NAME=name, KEY=ast.Str(s="__" + name)
            )


        # Visit macro body
        nodes = itertools.chain(*tuple(map(self.visit, node.body)))

        # Append visited nodes
        body += template("__i18n_domain = None")
        body += nodes

        function_name = "render" if node.name is None else \
                        "render_%s" % mangle(node.name)

        function = ast.FunctionDef(
            name=function_name, args=ast.arguments(
                args=[
                    param(self._current_stack),
                    param(self._defined_models[""]),
                    param("econtext"),
                    param("rcontext"),
                    ],
                defaults=[],
            ),
            body=body
            )

        yield function

    def visit_Text(self, node):
        #remove xml comment
        text = comment_re.sub("", node.value)
        return emit_node(ast.Str(s=text), STACK=self._current_stack)

    def visit_Domain(self, node):
        backup = "__previous_i18n_domain_%d" % id(node)
        return template("BACKUP = __i18n_domain", BACKUP=backup) + \
               template("__i18n_domain = NAME", NAME=ast.Str(s=node.name)) + \
               self.visit(node.node) + \
               template("__i18n_domain = BACKUP", BACKUP=backup)

    def visit_OnError(self, node):
        body = []

        fallback = identifier("__fallback")
        body += template("fallback = len(__stream)", fallback=fallback)

        self._enter_assignment((node.name, ))
        fallback_body = self.visit(node.fallback)
        self._leave_assignment((node.name, ))

        error_assignment = template(
            "econtext[key] = cls(__exc, rcontext['__error__'][-1][1:3])",
            cls=ErrorInfo,
            key=ast.Str(s=node.name),
            )

        body += self.visit(node.node)

        return body

    def visit_Content(self, node):
        name = "__content"
        body = self._engine(node.expression, store(name))

        if node.translate:
            body += emit_translate(name, name)

        if node.is_structure:
            body += emit_convert_structure(name, STACK=self._current_stack)
        else:
            body += emit_convert(name)
            body += template("STACK.t(NAME)", STACK=self._current_stack, NAME=name)

        return body

    def visit_Interpolation(self, node):
        name = identifier("content")
        res = self._engine(node, name) + \
               emit_node_if_non_trivial(name, STACK=self._current_stack)
        return res

    def visit_Alias(self, node):
        assert len(node.names) == 1
        name = node.names[0]
        target = self._aliases[-1][name] = identifier(name, id(node))
        return self._engine(node.expression, target)

    def visit_Assignment(self, node):
        for name in node.names:
            if name in COMPILER_INTERNALS_OR_DISALLOWED:
                raise TranslationError(
                    "Name disallowed by compiler.", name
                    )

            if name.startswith('__'):
                raise TranslationError(
                    "Name disallowed by compiler (double underscore).",
                    name
                    )

        assignment = self._engine(node.expression, store("__value"))

        if len(node.names) != 1:
            target = ast.Tuple(
                elts=[store_econtext(name) for name in node.names],
                ctx=ast.Store(),
            )
        else:
            target = store_econtext(node.names[0])

        assignment.append(ast.Assign(targets=[target], value=load("__value")))

        for name in node.names:
            if not node.local:
                assignment += template(
                    "rcontext[KEY] = __value", KEY=ast.Str(s=native_string(name))
                    )

        return assignment

    def visit_Define(self, node):
        scope = set(self._scopes[-1])
        self._scopes.append(scope)

        for assignment in node.assignments:
            if assignment.local:
                for stmt in self._enter_assignment(assignment.names):
                    yield stmt

            #ejos
            for stmt in self.visit(assignment):
                if isinstance(assignment, Alias) :
                    if  "default" in assignment.names or "attrs" in assignment.names:
                        continue
                yield stmt

        for stmt in self.visit(node.node):
            yield stmt

        for assignment in node.assignments:
            if assignment.local:
                for stmt in self._leave_assignment(assignment.names):
                    yield stmt

        self._scopes.pop()

    def visit_Omit(self, node):
        return self.visit_Condition(node)

    def visit_Condition(self, node):
        target = "__condition"
        assignment = self._engine(node.expression, target)

        assert assignment

        for stmt in assignment:
            yield stmt

        body = self.visit(node.node) or [ast.Pass()]

        orelse = getattr(node, "orelse", None)
        if orelse is not None:
            orelse = self.visit(orelse)

        test = load(target)

        yield ast.If(test=test, body=body, orelse=orelse)

    def visit_Translate(self, node):
        """Translation.

        Visit items and assign output to a default value.

        Finally, compile a translation expression and use either
        result or default.
        """

        body = []

        # Track the blocks of this translation
        self._translations.append(set())

        # Prepare new stream
        append = identifier("append", id(node))
        stream = identifier("stream", id(node))
        body += template("s = new_list", s=stream, new_list=LIST) + \
                template("a = s.append", a=append, s=stream)

        # Visit body to generate the message body
        code = self.visit(node.node)
        swap(ast.Suite(body=code), load(append), "__append")
        body += code

        # Reduce white space and assign as message id
        msgid = identifier("msgid", id(node))
        body += template(
            "msgid = __re_whitespace(''.join(stream)).strip()",
            msgid=msgid, stream=stream
        )

        default = msgid

        # Compute translation block mapping if applicable
        names = self._translations[-1]
        if names:
            keys = []
            values = []

            for name in names:
                stream, append = self._get_translation_identifiers(name)
                keys.append(ast.Str(s=name))
                values.append(load(stream))

                # Initialize value
                body.insert(
                    0, ast.Assign(
                        targets=[store(stream)],
                        value=ast.Str(s=native_string(""))))

            mapping = ast.Dict(keys=keys, values=values)
        else:
            mapping = None

        # if this translation node has a name, use it as the message id
        if node.msgid:
            msgid = ast.Str(s=node.msgid)

        # emit the translation expression
        body += template(
            "STACK.t(translate("
            "msgid, mapping=mapping, default=default, domain=__i18n_domain))",
            stack=self._current_stack,msgid=msgid, default=default, mapping=mapping
            )

        # pop away translation block reference
        self._translations.pop()

        return body

    def visit_Start(self, node):
        try:
            line, column = node.prefix.location
        except AttributeError:
            line, column = 0, 0

        yield Comment(
            " %s%s ... (%d:%d)\n"
            " --------------------------------------------------------" % (
                node.prefix, node.name, line, column))

        if not hasattr(node, "repeatable"):
            print "ea"
        if node.repeatable:
            push = template("STACK.repeat(N)", STACK=self._current_stack, N=ast.Str(s=node.name))
        elif node.replayable:
            push = template("STACK.replay(N)", STACK=self._current_stack, N=ast.Str(s=node.name))
        else:
            push = template("STACK.u(N)", STACK=self._current_stack, N=ast.Str(s=node.name))
        for stmt in push:
            yield stmt

        if node.attributes:
            for attribute in node.attributes:
                for stmt in self.visit(attribute):
                    yield stmt

    def visit_Attribute(self, node):
        f = node.space + "%s," + node.quote + "%s" + node.quote

        # Static attributes are just outputted directly
        if isinstance(node.expression, ast.Str):
            s = f % (node.name, node.expression.s)
            return template("STACK.a(N,S)", STACK=self._current_stack, N=ast.Str(s=node.name), S=ast.Str(s=node.expression.s))

        target = identifier("attr", node.name)
        body = self._engine(node.expression, store(target))
        return body + template(
            "STACK.a(NAME,  VALUE)",
            STACK=self._current_stack,
            NAME=ast.Str(s=node.name),
            VALUE=target,
            )

    def visit_Cache(self, node):
        body = []

        for expression in node.expressions:
            name = identifier("cache", id(expression))
            target = store(name)

            # Skip re-evaluation
            if self._expression_cache.get(expression):
                continue

            body += self._engine(expression, target)
            self._expression_cache[expression] = target

        body += self.visit(node.node)

        return body


    def visit_Name(self, node):
        """Translation name."""

        if not self._translations:
            raise TranslationError(
                "Not allowed outside of translation.", node.name)

        if node.name in self._translations[-1]:
            raise TranslationError(
                "Duplicate translation name: %s." % node.name)

        self._translations[-1].add(node.name)
        body = []

        # prepare new stream
        stream, append = self._get_translation_identifiers(node.name)
        body += template("s = new_list", s=stream, new_list=LIST) + \
                template("a = s.append", a=append, s=stream)

        # generate code
        code = self.visit(node.node)
        swap(ast.Suite(body=code), load(append), "__append")
        body += code

        # output msgid
        text = Text('${%s}' % node.name)
        body += self.visit(text)

        # Concatenate stream
        body += template("stream = ''.join(stream)", stream=stream)

        return body

    def visit_CodeBlock(self, node):
        stmts = template(textwrap.dedent(node.source.strip('\n')))

        for stmt in stmts:
            self._visitor(stmt)

        return stmts


    def visit_Repeat(self, node):
        # Used for loop variable definition and restore
        self._scopes.append(set())

        # Variable assignment and repeat key for single- and
        # multi-variable repeat clause
        if node.local:
            contexts = "econtext",
        else:
            contexts = "econtext", "rcontext"

        for name in node.names:
            if name in COMPILER_INTERNALS_OR_DISALLOWED:
                raise TranslationError(
                    "Name disallowed by compiler.", name
                    )

        if len(node.names) > 1:
            targets = [
                ast.Tuple(elts=[
                    subscript(native_string(name), load(context), ast.Store())
                    for name in node.names], ctx=ast.Store())
                for context in contexts
                ]

            key = ast.Tuple(
                elts=[ast.Str(s=name) for name in node.names],
                ctx=ast.Load())
        else:
            name = node.names[0]
            targets = [
                subscript(native_string(name), load(context), ast.Store())
                for context in contexts
                ]

            key = ast.Str(s=node.names[0])

        repeat = identifier("__repeat", id(node))
        index = identifier("__index", id(node))
        iterator = identifier("__iterator", id(node))
        assignment = [ast.Assign(targets=targets, value=load("__item"))]

        # Make repeat assignment in outer loop
        names = node.names
        local = node.local

        outer = self._engine(node.expression, store(iterator))

        if local:
            outer[:] = list(self._enter_assignment(names)) + outer

        outer += template(
            "REPEAT = econtext['repeat'](key, ITERATOR)",
            key=key, INDEX=index, REPEAT=repeat, ITERATOR=iterator
            )
        outer += template(
            "INDEX = REPEAT.length",
            INDEX=index, REPEAT=repeat
        )

        # Set a trivial default value for each name assigned to make
        # sure we assign a value even if the iteration is empty
        outer += [ast.Assign(
            targets=[store_econtext(name)
                     for name in node.names],
            value=load("None"))
              ]

        inner = template(
            "REPEAT._next()", REPEAT=repeat
        )
        # Compute inner body
        inner += self.visit(node.node)

        # After each iteration, decrease the index
        inner += template("index -= 1", index=index)

        # For items up to N - 1, emit repeat whitespace
        inner += template(
            "if INDEX > 0: STACK.t(WHITESPACE)", STACK=self._current_stack,
            INDEX=index, WHITESPACE=ast.Str(s=node.whitespace)
            )

        # Main repeat loop
        outer += [ast.For(
            target=store("__item"),
            iter=load(iterator),
            body=assignment + inner,
            )]

        # Finally, clean up assignment if it's local
        if outer:
            outer += self._leave_assignment(names)

        self._scopes.pop()

        return outer

    def _get_translation_identifiers(self, name):
        assert self._translations
        prefix = id(self._translations[-1])
        stream = identifier("stream_%d" % prefix, name)
        append = identifier("append_%d" % prefix, name)
        return stream, append

    def _enter_assignment(self, names):
        for name in names:
            for stmt in template(
                "BACKUP = getitem(econtext, KEY, __marker)",
                getitem=Symbol(getitem),
                BACKUP=identifier("backup_%s" % name, id(names)),
                KEY=ast.Str(s=native_string(name)),
                ):
                yield stmt

    def _leave_assignment(self, names):
        for name in names:
            for stmt in template(
                "deleteitem(econtext, KEY, BACKUP, __marker)",
                deleteitem=Symbol(deleteitem),
                BACKUP=identifier("backup_%s" % name, id(names)),
                KEY=ast.Str(s=native_string(name)),
                ):
                yield stmt
