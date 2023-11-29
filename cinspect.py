import argparse
from collections import OrderedDict

import sys
import pprint

import c_parser
import generators_imgui
import generators_printers

pp = pprint.PrettyPrinter()

if __name__ == "__main__":
    argparser = argparse.ArgumentParser("CInspect")
    argparser.add_argument(
        "filename", nargs="*", help="name of file to parse. you can also pass a glob"
    )
    argparser.add_argument(
        "--coord", help="show coordinates in the dump", action="store_true"
    )
    argparser.add_argument("--cpp-args", help="args to forward to cpp")

    argparser.add_argument(
        "-o",
        "--output",
        help="where to write the generated code",
    )
    # verbose
    argparser.add_argument(
        "-v",
        "--verbose",
        help="verbose",
        action="store_true",
    )

    args = argparser.parse_args()

    if args.filename is None:
        print("Please provide a filename or glob pattern")
        sys.exit()

    # filename arg can be a list of files
    files = args.filename

    c_parser.debug_print_enabled = args.verbose

    all_files_resolve_structs: OrderedDict[str, c_parser.StructInfo] = OrderedDict()
    for filename in files:
        ast = c_parser.get_ast(filename)
        resolved_structs = c_parser.resolve_structs(ast)
        # pretty print the resolved structs
        for struct_name, struct_info in resolved_structs.items():
            if struct_info.options.get("generate"):
                if args.verbose:
                    print(
                        f"Resolved struct {struct_name} @ {filename}:{struct_info.location.line}:{struct_info.location.column}",
                    )
                    pp.pprint(struct_info)

        all_files_resolve_structs.update(resolved_structs)

    if args.output:
        # generate imgui files
        generators_imgui.generate_imgui_files(args.output, all_files_resolve_structs)
        # generate printer files
        generators_printers.generate_printers_files(
            args.output, all_files_resolve_structs
        )
