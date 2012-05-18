from functools import partial
from chameleon.astutil import Builtin, Symbol, ItemLookupOnAttributeErrorVisitor
from chameleon.codegen import template
from chameleon.nodes import Module
from chameleon.parser import ElementParser
from chameleon.program import ElementProgram
from chameleon.tales import ExpressionParser
from chameleon.utils import read_bytes
from chameleon.zpt.program import MacroProgram

from compiler import Compiler, ExpressionEngine

import chameleon.tales
import pprint
import ast
from chameleon.zpt.template import Macros, PageTemplate
from prambanan.zpt import lookup_attr

__author__ = 'egoz'

def transform_attribute(node):
    return template(
        "lookup(object, name)",
        lookup=Symbol(lookup_attr),
        object=node.value,
        name=ast.Str(s=node.attr),
        mode="eval"
    )

class PythonExpr(chameleon.tales.PythonExpr):
    transform = ItemLookupOnAttributeErrorVisitor(transform_attribute)

class PTParser(object):

    default_encoding = "utf-8"

    def __init__(self, filename):
        source = self.read(filename)
        self.macros = {}
        self.expression_types = PageTemplate.expression_types.copy()
        self.expression_types["python"] = PythonExpr
        self.default_expression = PageTemplate.default_expression

        default_marker = Builtin("False")

        program = MacroProgram(
            source, "xml", filename,
            escape=True,
            default_marker=default_marker
        )
        module = Module("initialize", program)
        compiler = Compiler(self.engine, module, self._builtins(), strict=False)
        self.code = compiler.code

    def _builtins(self):
        return {
            'template': self,
            'macros': self.macros,
            'nothing': None,
            }

    @property
    def engine(self):
        default_marker = ast.Str(s="__default__")

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

