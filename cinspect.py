import argparse
from collections import OrderedDict
import glob
import sys
import pprint

import c_parser
import codegen

pp = pprint.PrettyPrinter()

# consider invoking with CPATH set to include pycparser/utils/fake_libc_include
# (note this is not included in the pycparser version installed from pip, just the git repo)

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

    printers_code = codegen.generate_code_for_structs(
        all_files_resolve_structs, codegen.generate_print_function
    )
    printers_headers = codegen.generate_code_for_structs(
        all_files_resolve_structs, codegen.generate_print_function_header
    )

    imgui_code = codegen.generate_code_for_structs(
        all_files_resolve_structs, codegen.generate_imgui_render_editor_code
    )
    imgui_headers = codegen.generate_code_for_structs(
        all_files_resolve_structs, codegen.generate_imgui_render_editor_code_header
    )

    if args.output:
        for struct_name, code in printers_code.items():
            deps = codegen.get_struct_dependencies(
                all_files_resolve_structs[struct_name], all_files_resolve_structs
            )
            with open(f"{args.output}/print_{struct_name}.c", "w") as f:
                for dep in deps:
                    f.write(f'// depends on "print_{dep}.c"\n')
                f.write(code)
            with open(f"{args.output}/print_{struct_name}.h", "w") as f:
                for dep in deps:
                    f.write(f'// depends on "print_{dep}.h"\n')
                f.write(printers_headers[struct_name])
        for struct_name, code in imgui_code.items():
            deps = codegen.get_struct_dependencies(
                all_files_resolve_structs[struct_name], all_files_resolve_structs
            )
            with open(f"{args.output}/imgui_{struct_name}.cpp", "w") as f:
                for dep in deps:
                    f.write(f'// depends on "imgui_{dep}.cpp"\n')
                f.write(code)
            with open(f"{args.output}/imgui_{struct_name}.h", "w") as f:
                for dep in deps:
                    f.write(f'// depends on "imgui_{dep}.h"\n')
                f.write(imgui_headers[struct_name])
    else:
        print("printers_code")
        pp.pprint(printers_code)
        print("imgui_code")
        pp.pprint(imgui_code)
