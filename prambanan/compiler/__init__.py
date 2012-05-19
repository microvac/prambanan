import os

class Module(object):
    def __init__(self, dependencies):
        if dependencies is None:
            dependencies = []
        self.dependencies = dependencies

class JavascriptModule(Module):
    def __init__(self, paths, dependencies=None):
        if isinstance(paths, str):
            paths = [paths]
        self.paths = paths
        super(JavascriptModule, self).__init__(dependencies)

    def files(self):
        for path in self.paths:
            yield ("js", path)

class PythonModule(Module):
    def __init__(self, paths, dependencies=None):
        if isinstance(paths, str):
            paths = [paths]
        self.paths = paths
        super(PythonModule, self).__init__(dependencies)

    def files(self):
        for path in self.paths:
            yield ("py", path)

class DirectoryModule(Module):
    def __init__(self, children, dependencies=None):
        self.children = children
        super(DirectoryModule, self).__init__(dependencies)

    @staticmethod
    def load(dir, dependencies=None):
        config = os.path.abspath(os.path.join(dir, "__prambanan__.py"))
        glbl = {"__file__": config}
        execfile(config, glbl)
        children = glbl["children"]
        return DirectoryModule(children, dependencies)

    def files(self):
        for child in self.children:
            for child_item in child.files():
                yield child_item

def files_to_modules(files):
    for file in  files:
        if os.path.isdir(file):
            yield DirectoryModule.load(file)
        else:
            name, ext = os.path.splitext(os.path.basename(file))
            if ext == ".py":
                yield PythonModule(file)
            elif ext == ".js":
                yield JavascriptModule(file)
            else:
                raise ValueError("extension not recognized: %s for file %s" % (ext, file))

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



