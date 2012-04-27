#

class ParseError(Exception):
    """
    This exception is raised if the parser detects fatal errors.

    """
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)

def JSNative(s):
    return s

def JSNoOp(target):
    return target