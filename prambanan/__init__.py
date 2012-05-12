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


def JSNative(s):
    return s

def JSNoOp(target):
    return target