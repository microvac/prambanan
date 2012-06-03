from StringIO import StringIO
import unittest
from logilab.astng import nodes, builder
from prambanan.compiler.scopegenerator import ScopeGenerator
from prambanan.compiler.target import JSDefaultTranslator
from prambanan.compiler.utils import ParseError

def visit_module(self, mod):
    """
    Initial node.
    There is and can be only one Module node.

    """
    self.curr_scope = self.mod_scope

    for stmt in mod.body:
        self.visit(stmt)
        if not isinstance(stmt, nodes.Import) and not isinstance(stmt, nodes.From) and not isinstance(stmt, nodes.Pass):
            self.write_semicolon(stmt)

    builtin_var = None
    builtins = set(self.mod_scope.all_used_builtins())
    if len(builtins) > 0:
        builtin_var = self.curr_scope.generate_variable("__builtin__")
        for builtin in builtins:
            self.curr_scope.declare_variable(builtin)

    self.change_buffer(self.HEADER_BUFFER)
    self.write_variables()

    if len(builtins) > 0:
        self.write("%s = %s.import('__builtin__');" %(builtin_var, self.lib_name))
        for builtin in builtins:
            self.write("%s = %s.%s;" %(builtin, builtin_var, builtin))

    for item in self.util_names.values():
        name, value = item
        self.write("%s = %s;" %(name, value))

    self.flush_all_buffer()
    self.curr_scope = None

def translate_string(target_cls, input_lines):
    config = {}
    output = StringIO()
    config["bare"] = True
    config["input_name"] = "source.py"
    config["input_lines"] = input_lines
    config["output"] = StringIO()
    config["namespace"] = ""
    config["use_throw_helper"] = True
    config["warnings"] = {}

    tree = builder.ASTNGBuilder().string_build("\n".join(input_lines))

    scope_gen = ScopeGenerator(config["namespace"], tree)
    scope_gen.visit(tree)

    direct_handlers = {"module": visit_module}
    moo = target_cls(scope_gen.root_scope, direct_handlers, config)
    moo.walk(tree)

    return config["output"].getvalue()

def make_tester(target_cls, lines, translate_specs, translate_errors):
    def tester(self):
        for start, end in translate_specs:
            spec_lines = lines[start+1:end]
            i = 0
            for line in spec_lines:
                if line.strip() == "->":
                    separator = i
                i+=1
            py = []
            js = []
            first_white_space = len(spec_lines[0]) - len(spec_lines[0].lstrip())
            for i in range(0, separator):
                py.append(spec_lines[i][first_white_space:])
            for i in range(separator+1, len(spec_lines)):
                js.append(spec_lines[i].strip())

            translated =  translate_string(target_cls, py)
            print ""
            print "--python------"
            print "\n".join(py)
            print "--js----------"
            print "\n".join(js)
            print "--translated--"
            print translated
            self.assertEquals(" ".join(js), translated)
        for start, end in translate_errors:
            spec_lines = lines[start+1:end]
            py = []
            first_white_space = len(spec_lines[0]) - len(spec_lines[0].lstrip())
            for i in range(0, len(spec_lines)):
                py.append(spec_lines[i][first_white_space:])
            print ""
            print "--python error--"
            print "\n".join(py)
            self.assertRaises(ParseError, translate_string, target_cls, py)
    return tester


def translate_spec_tester(target_cls):
    def dec(cls):
        for name, attr in target_cls.__dict__.items():
            doc = getattr(attr, "__doc__", None)
            if doc is not None:
                doc_lines = doc.splitlines()

                translate_specs = []
                translate_errors = []
                last_start = -1
                last_empty = -1
                last_type = ""
                i = 0
                for line in doc_lines:
                    is_translate_spec = line.strip().startswith("@translate-spec")
                    is_translate_error = line.strip().startswith("@translate-error")
                    if last_start != -1:
                        if is_translate_spec or is_translate_error:
                            if last_type == "spec":
                                translate_specs.append((last_start, i - 1))
                            elif last_type == "error":
                                translate_errors.append((last_start, i - 1))
                            last_empty = -1
                            last_start = i
                            last_type = "spec" if is_translate_spec else "error"
                        elif line.strip() == "":
                            if last_empty == -1:
                                last_empty = i
                            else:
                                if last_type == "spec":
                                    translate_specs.append((last_start, last_empty))
                                elif last_type == "error":
                                    translate_errors.append((last_start, last_empty))
                                last_start = last_empty = -1
                                last_type = ""

                    elif is_translate_spec:
                        last_start = i
                        last_type = "spec"
                    elif is_translate_error:
                        last_start = i
                        last_type = "error"
                    i+=1
                if last_start != -1:
                    if last_type == "spec":
                        translate_specs.append((last_start, i - 1))
                    elif last_type == "error":
                        translate_errors.append((last_start, i - 1))

                if len(translate_specs) > 0 or len(translate_specs) > 0:
                    setattr(cls, "test_"+name,  make_tester(target_cls, doc_lines, translate_specs, translate_errors))
        return cls
    return dec

@translate_spec_tester(JSDefaultTranslator)
class JSDefaultTester(unittest.TestCase):
    pass