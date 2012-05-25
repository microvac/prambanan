from StringIO import StringIO
import os
import sys
import argparse
import gettext
import pkg_resources

from collections import OrderedDict
from prambanan.compiler.utils import ParseError

from prambanan.jsbeautifier import beautify
from prambanan.compiler import (
    files_to_modules,
    translate)
from prambanan.compiler.provider import all_providers


def construct_parser():
    parser = argparse.ArgumentParser(
        description="Compiles python to javascript.")

    parser.add_argument('files', metavar='f', type=str, nargs='*',
        help='input filenames')

    parser.add_argument("-o", "--output",
        type=argparse.FileType('w'), default=sys.stdout,
        help="output file, or std output if empty")
    parser.add_argument("-n", "--namespace", dest="base_namespace",
        default = "", type=str,
        help="base export namespace, something that appends to filename")

    parser.add_argument("-t", "--target", dest="target",
        default = "", type=str,
        help="js target")

    parser.add_argument("-l", "--locale-languange", dest="locale_language",
        default = None, type=str,
        help="target languange")
    parser.add_argument("--locale-domain", dest="locale_domain",
        default = None, type=str,
        help="locale domain, default=as namespace")
    parser.add_argument("--locale-dir", dest="locale_dir",
        default = None, type=str,
        help="locale directory default = pkg_resource of namespace")

    parser.add_argument("--no-wrap", action="store_true", dest="bare",
        help="don't wrap result")
    parser.add_argument("--no-beautify", action="store_false", dest="beautify",
        help="don't beautify result")

    parser.add_argument("--no-generate-result", action="store_false", dest="generate_result",
        help="don't generate result")
    parser.add_argument("--generate-imports", action="store_true",
        help="also generate imported module")
    parser.add_argument("--generate-base", action="store_true",
        help="also generate base library")

    parser.add_argument("--type-warning", action="store_true",
        help="warn when not finding type")
    parser.add_argument("--import-warning", action="store_true",
        help="warn when cannot resolve import")

    return parser

def walk_import(import_name, modules):
    if import_name in modules:
        module = modules[import_name]
        for dependency in module.dependencies:
            for dep_name, dep_module in walk_import(dependency, modules):
                yield (dep_name, dep_module)
        yield (import_name, module)

def walk_imports(import_names, modules):
    results = OrderedDict()
    for import_name in import_names:
        for name, value in  walk_import(import_name, modules):
            if name not in results:
                results[name] = value
    return results

def translate_py_file(args, filename, output, overridden_types):
    base_namespace = args.base_namespace

    warnings = {}
    if args.type_warning:
        warnings["type"] = True
    if args.import_warning:
        warnings["import"] = True

    base_name = os.path.basename(filename)
    dir_name = os.path.dirname(filename)
    name, ext = os.path.splitext(base_name)
    namespace = name if base_namespace == "" else "%s.%s" % (base_namespace, name)

    translator = None
    if args.locale_language is not None:
        lang = args.locale_language
        locale_domain = args.locale_domain
        locale_dir = args.locale_dir
        if locale_domain is None:
            locale_domain = namespace
        if locale_dir is None:
            try:
                locale_dir = pkg_resources.resource_filename(locale_domain, "locale/")
            except ImportError:
                pass
        if locale_dir is not None:
            try:
                translator = gettext.translation(locale_domain, locale_dir, [lang]).gettext
            except IOError:
                pass

    if translator is None:
        translator = gettext.NullTranslations().gettext

    with open(filename, 'r') as f:
        lines = f.readlines()
    input = StringIO("".join(lines)).read()

    native = None
    if base_name == "__init__":
        native_file = os.path.join(dir_name, "native.js")
    else:
        native_file = os.path.join(dir_name, name+"_native.js")
    if os.path.isfile(native_file):
        with open(native_file, "r") as f:
            native = f.readlines()
    config = {
        "namespace": namespace,
        "input_name": base_name,
        "input_lines": lines,
        "input": input,
        "warnings": warnings,
        "indent": "\t",
        "bare": args.bare,
        "output": output,
        "native": native,
        "overridden_types": overridden_types,
        "translator": translator,
        "target": args.target,
        }

    return translate(config)

def translate_modules(modules, args, output, overridden_types):
    imports = []
    tmp_out = StringIO() if args.beautify else output
    for module in  modules:
        for type, file in module.files():
            if type == "js":
                with open(file, "r") as f:
                    tmp_out.write(f.read())
            elif type == "py":
                file_imports = translate_py_file(args, file, tmp_out, overridden_types)
                for imp in file_imports:
                    imports.append(imp)
            else:
                raise ValueError("type %s is not supported for file %s" % (type % file))
    if args.beautify:
        output.write(beautify(tmp_out.getvalue()))
    return imports

def generate_base(out):
    #used_modules = walk_imports(import_names, available_modules)
    pass

def generate_imports(args, out, import_names, available_modules, overridden_types):
    used_modules = walk_imports(import_names, available_modules)
    for name, module in used_modules.items():
        sys.stderr.write("generating %s" % name)
        translate_modules([module], args, out, overridden_types)

def show_parse_error(e):
    if e.lineno is not None:
        sys.stderr.write("%-6s  " % "")
        sys.stderr.write("file '%s' line %d column %d:\n" %  (e.input_name, e.lineno, e.col_offset))
        lines = e.input_lines
        end_line = e.lineno
        start_line = e.lineno - 5
        if start_line < 0:
            start_line = 0
        for i in range(start_line, end_line):
            sys.stderr.write("%-6d: %s" % (i+1, lines[i]))
        sys.stderr.write("%-6s  " % "")
        for i in range(0, e.col_offset):
            sys.stderr.write(" ")
        sys.stderr.write("^\n")
    sys.stderr.write(str(e))
    sys.stderr.write("\n")

def main(argv=sys.argv[1:]):
    parser = construct_parser()
    args = parser.parse_args(argv)
    providers = all_providers()
    modules = dict([ (n,m) for p in providers for n,m in p.get_modules().items()])
    overridden_types = dict([ (n,f) for p in providers for n,f in p.get_overridden_types().items()])
    try:
        translate_out = StringIO() if args.generate_result else open(os.devnull, "w")
        imports = translate_modules(files_to_modules(args.files), args, translate_out, overridden_types)
        if args.generate_base:
            generate_base(args.output)
        if args.generate_imports:
            generate_imports(args, args.output, imports, modules, overridden_types)
        if args.generate_result:
            args.output.write(translate_out.getvalue())
    except ParseError as e:
        show_parse_error(e)
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]) or 0)

