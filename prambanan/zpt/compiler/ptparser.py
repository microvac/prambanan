from functools import partial
from chameleon.astutil import Builtin, ItemLookupOnAttributeErrorVisitor, Symbol, AnnotationAwareVisitor, ASTCodeGenerator
from chameleon.codegen import template
from chameleon.exc import TemplateError
from chameleon.nodes import Module
from chameleon.tales import ExpressionParser
from chameleon.utils import read_bytes

from compiler import Compiler, ExpressionEngine

import ast
import re
from chameleon.zpt.template import  PageTemplate
from prambanan.zpt import lookup_attr
from prambanan.zpt.compiler.program import BindingProgram
from chameleon.tales import PythonExpr


lookup_attr.__module__ = "prambanan.zpt"

__author__ = 'egoz'

def transform_attribute(node):
    info = "\n".join(ASTCodeGenerator(node).lines)
    return template(
        "lookup(object, name, info, __filename)",
        lookup=Symbol(lookup_attr),
        object=node.value,
        name=ast.Str(s=node.attr),
        info=ast.Str(s=info),
        mode="eval"
    )

model_re = re.compile(r"#([\w]*)", re.MULTILINE)
def replace_model_re(m):
    model_name = m.groups()[0]
    result = "__model_" + model_name
    return result

class AttributeAndCallVisitor(AnnotationAwareVisitor):
    def __init__(self, transform):
        self.transform = transform

    def visit_Attribute(self, node):
        self.generic_visit(node)
        self.apply_transform(node)

    def visit_Call(self, node):
        if isinstance(node.func, ast.Attribute):
            self.generic_visit(node.func)
        for arg in node.args:
            self.visit(arg)

class PrambananExpr(PythonExpr):
    """
    change all
        @expr -> model.get(expr)
        @a.b.c to model.get('a').get('b').get('c)
    before passing to python expr
    """
    transform = AttributeAndCallVisitor(transform_attribute)

    def translate(self, expression, target):
        expression = model_re.sub(replace_model_re, expression)
        return PythonExpr.translate(self, expression, target)


class PTParser(object):

    default_encoding = "utf-8"

    def __init__(self, filename, binds=False):
        source = self.read(filename)
        self.macros = {}
        self.expression_types = PageTemplate.expression_types.copy()
        self.expression_types["prambanan"] = PrambananExpr
        self.default_expression = "prambanan"

        default_marker = Builtin("False")

        try:
            program = BindingProgram(
                source, "xml", filename,
                escape=True,
                default_marker=default_marker,
                binds=binds,
            )
            module = Module("initialize", program)
            compiler = Compiler(self.engine, module, self._builtins(), strict=False, source=source, filename=filename)
            self.code = compiler.code
        except TemplateError as e:
            raise

    def _builtins(self):
        return {
            'template': self,
            'macros': self.macros,
            'nothing': None,
            }

    @property
    def engine(self):
        default_marker = Builtin("False")

        return partial(
            ExpressionEngine,
            self.expression_parser,
            default_marker=default_marker,
        )

    @property
    def expression_parser(self):
        return ExpressionParser(self.expression_types, self.default_expression)


    def read(self, filename):
        with open(filename, "rb") as f:
            data = f.read()

        body, encoding, content_type = read_bytes(
            data, self.default_encoding
        )

        # In non-XML mode, we support various platform-specific line
        # endings and convert them to the UNIX newline character
        if content_type != "text/xml" and '\r' in body:
            body = body.replace('\r\n', '\n').replace('\r', '\n')

        self.content_type = content_type
        self.content_encoding = encoding

        return body

