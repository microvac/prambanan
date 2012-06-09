import unittest
from pyparsing import alphas, Word, alphanums, Forward, Literal, commaSeparatedList, Group, Suppress, OneOrMore, Optional

from logilab.astng.builder import ASTNGBuilder
from prambanan.cmd import patch_astng_manager
import prambanan.compiler.astng_patch
from prambanan.compiler.hint import TypeHintProcessor
from prambanan.compiler.manager import PrambananManager

manager = PrambananManager([])
processor = TypeHintProcessor()
patch_astng_manager(manager)
builder = ASTNGBuilder(manager)


code = ''''''

astng = builder.string_build(code, __name__, __file__)


ELEMENT = Forward()
EREF = Group(ELEMENT)

ID = Word(alphanums+".")
TYPE = Group((ID+Suppress(":")+ID | ID))

INSTANCE = ("i("+TYPE+")")
CLASS = "c("+TYPE+")"
LIST = "l("+EREF+")"
DICT ="d("+EREF+","+EREF+")"
TUPLE = "t("+OneOrMore(EREF+Suppress(Optional(",")))+")"
ELEMENT << (INSTANCE | CLASS | LIST | DICT | TUPLE)

print ELEMENT.parseString("i(borobudur.page:Page)")
print ELEMENT.parseString("c(borobudur.page:Page)")
print ELEMENT.parseString("l(i(borobudur.page:Page))")
print ELEMENT.parseString("l(i(string))")
print ELEMENT.parseString("d(l(i(string)),i(int))")
print ELEMENT.parseString("t(i(string))")
print ELEMENT.parseString("t(i(string), i(string))")


class TestTypeHintProcessor(unittest.TestCase):

    def test_instance(self):
        hint = "anu i(int)"
        print processor.process(astng, hint)
        hint = "anu i(borobudur.page:Page)"
        print processor.process(astng, hint)

    def test_list(self):
        hint = "anu l(i(int))"
        print processor.process(astng, hint)

    def test_tuple(self):
        hint = "anu t(i(int),i(int))"
        print processor.process(astng, hint)

