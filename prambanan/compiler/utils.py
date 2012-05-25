from exceptions import Exception
import re

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


def get_op(op):
    """
    Translates an operator.

    """
    return OP_MAP[op][0]


def get_op_cpa(op):
    """
    Get operator chars, precedence and associativity.

    """
    return OP_MAP[op]

def get_expr_pa(expr):
    """
    Get the precedence and associativity of an expression.

    """
    name = expr.__class__.__name__
    if name in ("BoolOp", "BinOp", "UnaryOp"):
        return get_op_cpa(expr.op)[1:]
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


class ParseError(Exception):
    """
    This exception is raised if the parser detects fatal errors.

    """
    def __init__(self, value, lineno=None, col_offset=0, is_syntax_error = False, input_lines=None, input_name=None):
        self.value = value
        self.lineno = lineno
        self.col_offset = col_offset
        self.is_syntax_error = is_syntax_error
        if input_lines is None:
            input_lines = []
        self.input_lines = input_lines
        self.input_name = input_name

    def __str__(self):
        msg = "%s: %s" % ("Syntax Error" if self.is_syntax_error else "Translation Error", self.value)
        return msg


class Writer(object):
    def __init__(self, default_buffer_name, buffer_names):
        self.buffers = dict([(buffer, []) for buffer in buffer_names])
        self.buffer = self.buffers[default_buffer_name]
        self.indent_level = 0

    def change_buffer(self, name):
        self.buffer = self.buffers[name]

    def write(self, s):
        self.buffer.append(s)

    def indent(self, updown = True):
        if updown:
            self.indent_level += 1
        else:
            self.indent_level -= 1