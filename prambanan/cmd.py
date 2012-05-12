from StringIO import StringIO
import os
import sys
import logging
import argparse
import jsbeautifier
import pprint
from prambanan import ParseError

from prambanan.translator import translate_file


def usage(argv):
    cmd = os.path.basename(argv[0])
    print('usage: %s <config_uri> <watch|clean|build|check>\n'
          '(example: "%s development.ini clean")' % (cmd, cmd))
    sys.exit(1)

demo_config = {
    "export_map": {},
    "indent": "\t",
    "out_filename": "",
    "in_filenames":[],
    "warnings": True,
    "bare": False
    }

def construct_parser():
    parser = argparse.ArgumentParser(
        description="Manage assets.")

    parser.add_argument("-n", "--namespace", dest="namespace",
        default = None, type=str,
        help="export namespace")
    parser.add_argument("-b", "--base-namespace", dest="base_namespace",
        default = "", type=str,
        help="base export namespace")
    parser.add_argument("-c", "--python-config", dest="python_config",
        default = None, type=str,
        help="python config file")
    parser.add_argument("-o", "--output", dest="output",
        type=str, default=None,
        help="output file, or std output if empty")
    parser.add_argument("--indent", dest="indent",
        type=str, default="\t",
        help="indentation chars")
    parser.add_argument("--type-warning", dest="type_warning",
        default = False, const=True, type=bool, nargs="?",
        help="warn when not finding type")
    parser.add_argument("--bare", dest="bare",
        default = False, const=True, type=bool, nargs="?",
        help="don't wrap result")
    parser.add_argument('files', metavar='f', type=str, nargs='*',
        help='input filenames')
    return parser

class FileBuffer(StringIO):
    def __init__(self, filename):
        self.filename = filename
        StringIO.__init__(self)


def process_config(parser, config):
    result = {"__file__": os.path.abspath(config)}
    execfile(config, result)
    for item in result["configs"]:
        default = parser.parse_args("")
        default.__dict__.update(item)
        yield default

def process_file(args, output):
    base_namespace = args.base_namespace
    warnings = {}
    if args.type_warning:
        warnings["type"] = True

    for filename in args.files:
        file = open(filename, 'r')
        namespace = args.namespace
        if namespace is None:
            name, ext = os.path.splitext(os.path.basename(file.name))
            namespace = name if base_namespace == "" else "%s.%s" % (base_namespace, name)
        lines = file.readlines()
        input = StringIO("".join(lines)).read()
        file.close()
        yield {
            "namespace": namespace,
            "input_name": os.path.basename(file.name),
            "input_lines": lines,
            "input": input,
            "warnings": warnings,
            "indent": args.indent,
            "bare": args.bare,
            "output": output,
            }

def process(parser, args, out_files, out=None):
    if args.python_config is not None:
        for item in process_config(parser, args.python_config):
            if out is None:
                out = FileBuffer(None) if item.output is None else FileBuffer(item.output)
                out_files.append(out)
            for processed in process(parser, item, out_files, out):
                yield processed
    else:
        if out is None:
            out = FileBuffer(None)
            out_files.append(out)
        for result in process_file(args, out):
            yield result



def main(argv=sys.argv[1:]):
    parser = construct_parser()
    out_files = []
    args = parser.parse_args(argv)

    try:
        for config in process(parser, args, out_files):
            try:
                translate_file(config)
            except ParseError as e:
                if e.lineno is not None:
                    sys.stderr.write("%-6s  " % "")
                    sys.stderr.write("file '%s' line %d column %d:\n" %  (config["input_name"], e.lineno, e.col_offset))
                    lines = config["input_lines"]
                    endline = e.lineno
                    startline = e.lineno - 5
                    if startline < 0:
                        startline = 0
                    for i in range(startline, endline):
                        sys.stderr.write("%-6d: %s" % (i+1, lines[i]))
                    sys.stderr.write("%-6s  " % "")
                    for i in range(0, e.col_offset):
                        sys.stderr.write(" ")
                    sys.stderr.write("^\n")
                sys.stderr.write(str(e))
                sys.stderr.write("\n")
                return 1
    finally:
        for out_file in out_files:
            if isinstance(out_file, FileBuffer):
                if out_file.filename is None:
                    f = sys.stdout
                else:
                    f = open(out_file.filename, "w")
                f.write(jsbeautifier.beautify(out_file.getvalue()))
                f.close()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]) or 0)

