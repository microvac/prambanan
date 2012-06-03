import prambanan.compiler.astng_patch

from StringIO import StringIO
import os
import sys
import argparse
import gettext
import pkg_resources
import logilab.astng.scoped_nodes

from collections import OrderedDict
from prambanan.compiler.manager import PrambananManager
from prambanan.compiler.utils import ParseError

from .jsbeautifier import beautify
from .compiler import (
    files_to_modules,
    translate, JavascriptModule, PythonModule, RUNTIME_MODULES)
from .compiler.provider import all_providers
from .output import DirectoryOutputManager, SingleOutputManager

def create_translate_parser():
    parser = argparse.ArgumentParser(
        description="Translate python to javascript.")

    parser.add_argument("-t", "--target", dest="target",
        default = "", type=str,
        help="js target")

    parser.add_argument("-l", "--locale-languange", dest="locale_language",
        default = None, type=str,
        help="target languange")
    parser.add_argument("--locale-domain", dest="locale_domain",
        default = None, type=str,
        help="locale domain, default=as modname")
    parser.add_argument("--locale-dir", dest="locale_dir",
        default = None, type=str,
        help="locale directory default = pkg_resource of modname")

    parser.add_argument("--no-wrap", action="store_true", dest="bare",
        help="don't wrap result")
    parser.add_argument("--no-beautify", action="store_false", dest="beautify",
        help="don't beautify result")

    parser.add_argument("--type-warning", action="store_true",
        help="warn when not finding type")
    parser.add_argument("--import-warning", action="store_true",
        help="warn when cannot resolve import")

    return parser

def create_generate_parser():
    parser = create_translate_parser()

    parser.add_argument("--no-generate-result", action="store_false", dest="generate_result",
        help="don't generate result")
    parser.add_argument("--generate-imports", action="store_true",
        help="also generate imported module")
    parser.add_argument("--generate-runtime", action="store_true",
        help="also generate runtime library")
    parser.add_argument("--imports", dest="imports",
        default = "", type=str,
        help="explicit imports (comma separated)")

    return parser

def create_main_parser():
    parser = create_generate_parser()
    parser.add_argument("-o", "--output_file",
        type=str, default=None,
        help="output file, or std output if empty")
    parser.add_argument("-d", "--output_dir",
        type=str, default=None,
        help="output directory, or std output if empty")
    parser.add_argument('files', metavar='f', type=str, nargs='*',
        help='input filenames')
    return parser

translate_parser = create_translate_parser()
generate_parser = create_generate_parser()
main_parser = create_main_parser()

def parse_args(argv, parser):
    args = parser.parse_args(argv)
    args.modname = None
    return args

def merge_args(args, d):
    for name in args.__dict__:
        if name in d:
            args.__dict__[name] = d[name]

def copy_args(source, parser, **kwargs):
    args = parse_args("", parser)
    merge_args(args, source.__dict__)
    merge_args(args, dict(kwargs))
    return args

def create_args(parser,**kwargs):
    args = parse_args("", parser)
    merge_args(args, dict(kwargs))
    return args

def patch_astng_manager(manager):
    logilab.astng.scoped_nodes.MANAGER = manager

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

def translate_py_file(translate_args, output, manager, filename, modname, overridden_types):
    #warnings
    warnings = {}
    if translate_args.type_warning:
        warnings["type"] = True

    #input
    with open(filename, 'r') as f:
        lines = f.readlines()
    input = StringIO("".join(lines)).read()

    #i18n translator
    translator = None
    if translate_args.locale_language is not None:
        lang = translate_args.locale_language
        locale_domain = translate_args.locale_domain
        locale_dir = translate_args.locale_dir
        if locale_domain is None:
            locale_domain = modname
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


    #native file
    base_name = os.path.basename(filename)
    dir_name = os.path.dirname(os.path.abspath(filename))
    name, ext = os.path.splitext(base_name)

    native = None
    if base_name == "__init__.py":
        native_file = os.path.join(dir_name, "native.js")
    else:
        native_file = os.path.join(dir_name, name+"_native.js")
    if os.path.isfile(native_file):
        with open(native_file, "r") as f:
            native = f.readlines()

    config = {
        "bare": translate_args.bare,
        "output": output,
        "target": translate_args.target,
        "modname": modname,
        "input_name": base_name,
        "input_lines": lines,
        "input": input,
        "warnings": warnings,
        "indent": "\t",
        "native": native,
        "overridden_types": overridden_types,
        "translator": translator,
        }

    return translate(config, manager)

def get_ovverridden_types():
    providers = all_providers()
    overridden_types = dict([ (n,f) for p in providers for n,f in p.get_overridden_types().items()])
    return overridden_types

def get_available_modules():
    providers = all_providers()
    available_modules = dict([ (m.modname,m) for p in providers for m in p.get_modules()])
    return available_modules


def generate_modules(translate_args, output_manager, manager, modules):
    patch_astng_manager(manager)

    overridden_types = get_ovverridden_types()

    for module in  modules:
        for type, file, modname in module.files():
            if type == "js":
                preferred_name, ext = os.path.splitext(os.path.basename(file))
            elif type == "py":
                preferred_name = modname
            else:
                raise ValueError("type %s is not supported for file %s" % (type % file))

            out_file = output_manager.add(file, preferred_name)

            if not manager.is_file_changed(file) and output_manager.is_output_exists(file):
                continue

            output_manager.start(out_file)
            if type == "js":
                with open(file, "r") as f:
                    output_manager.out.write(f.read())
            elif type == "py":
                output = StringIO() if translate_args.beautify else output_manager.out
                translate_py_file(translate_args, output, manager, file, modname, overridden_types)
                if translate_args.beautify:
                    output_manager.out.write(beautify(output.getvalue()))
            else:
                raise ValueError("type %s is not supported for file %s" % (type % file))
            output_manager.stop()

def generate_runtime(translate_args, output_manager, manager):
    generate_modules(translate_args, output_manager, manager, RUNTIME_MODULES)


def generate_imports(translate_args, output_manager, manager, import_names):
    available_modules = get_available_modules()

    used_modules = walk_imports(import_names, available_modules)
    for name in import_names:
        if name not in used_modules and translate_args.import_warning:
            sys.stderr.write("WARN: cannot find module %s for import  \n" % name)

    generate_modules(translate_args, output_manager, manager, used_modules.values())

def generate(generate_args, output_manager, manager, modules):
    modules = list(modules)

    translate_args = copy_args(generate_args, translate_parser)
    imports = [d for m in modules for d in m.dependencies]
    if generate_args.generate_runtime:
        generate_runtime(translate_args, output_manager, manager)
    if generate_args.generate_imports:
        generate_imports(translate_args, output_manager, manager, imports)
    if generate_args.generate_result:
        generate_modules(translate_args, output_manager, manager, modules)

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
    main_args = parse_args(argv, main_parser)
    modules = list(files_to_modules([os.path.abspath(f) for f in main_args.files], os.path.abspath("")))
    manager = PrambananManager(modules)

    if main_args.output_file is not None:
        output_manager = SingleOutputManager(open(main_args.output_file, "w"))
    elif main_args.output_dir is not None:
        if not os.path.exists(main_args.output_dir):
            os.mkdir(main_args.output_dir)
        output_manager = DirectoryOutputManager(main_args.output_dir)
    else:
        output_manager = SingleOutputManager(sys.stdout)

    generate_args = copy_args(main_args, generate_parser)
    try:
        generate(generate_args, output_manager, manager, modules)
    except ParseError as e:
        show_parse_error(e)
        return 1
    finally:
        if main_args.output_file is not None:
            output_manager.out.close()

    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]) or 0)
