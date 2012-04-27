import os
import sys
import logging

from prambanan.translator import translate_files


def usage(argv):
    cmd = os.path.basename(argv[0])
    print('usage: %s <config_uri> <watch|clean|build|check>\n'
          '(example: "%s development.ini clean")' % (cmd, cmd))
    sys.exit(1)

demo_config = {
    "export_map": {},
    "namespace": "demo",
    "indent": "\t",
    "out_filename": "",
    "in_filenames":[],
    "warnings": True,
    }

def main(argv=sys.argv):
    config = demo_config
    config["in_filenames"].append(argv[1])
    config["out_filename"] = argv[2]
    translate_files(config)
