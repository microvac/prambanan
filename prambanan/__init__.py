#

class ParseError(Exception):
    """
    This exception is raised if the parser detects fatal errors.

    """
    def __init__(self, value, lineno=None, col_offset=0, is_syntax_error = False):
        self.value = value
        self.lineno = lineno
        self.col_offset = col_offset
        self.is_syntax_error = is_syntax_error

    def __str__(self):
        msg = "%s: %s" % ("Syntax Error" if self.is_syntax_error else "Translation Error", self.value)
        return msg

def JSNative(s):
    return s

def JSNoOp(target):
    return target