from collections import OrderedDict

import typeassert
from c_parser import StructInfo
import codegen


printf_formatters = {
    "signed": "%d",
    "unsigned": "%u",
    "int": "%d",
    "unsigned int": "%u",
    "long": "%ld",
    "unsigned long": "%lu",
    "short": "%hd",
    "unsigned short": "%hu",
    "float": "%f",
    "double": "%f",
    "char*": "%s",
    "cstring": "%s",
    "void": "void",
}


# Generate C code for printing function
def generate_print_function(
    struct_info: StructInfo, all_structs: OrderedDict[str, StructInfo]
) -> str:
    c_code = f""
    # Define a print function for the struct
    c_code += f"void print_{struct_info.name}(const {struct_info.name} *data, int rec_depth, int max_depth) {{\n"
    c_code += f"  if (max_depth == 0) max_depth = 2;\n"
    c_code += f"  if (rec_depth > max_depth) {{ return; }}\n"
    c_code += f'  for (int i = 0; i < rec_depth; i++) {{ printf("  "); }}\n'
    c_code += f'  printf("{struct_info.name} {{\\n");\n'

    # Define print statements for each field
    for field in struct_info.fields:
        c_code += f'  for (int i = 0; i < rec_depth+1; i++) {{ printf("  "); }}\n'
        c_code += f'  printf("{field.name}: '
        if field.reference_depth > 1:
            c_code += f'Array<{field.custom_type or field.type_handler}>\\n");\n'
            continue

        # perform indentation based on rec_depth
        dereferences = "*" * field.reference_depth
        if field.type_handler in printf_formatters:
            c_code += f'{printf_formatters[field.type_handler]}\\n", {dereferences}data->{field.name});\n'
        elif field.type_handler == "struct" and field.custom_type in all_structs:
            # print the struct
            # assumes you have also generated a print... function for each custom struct
            c_code += f'\\n");\n'
            c_code += f"  print_{field.custom_type}(&{dereferences}data->{field.name}, rec_depth+1);\n"
        else:
            c_code += f'Unsupported type\\n");\n'

    c_code += f'  printf("}}\\n");\n'
    c_code += f"}}\n\n"

    return c_code


def generate_print_function_header(
    struct_info: StructInfo, all_structs: OrderedDict[str, StructInfo]
) -> str:
    c_code = f"void print_{struct_info.name}(const {struct_info.name} *data, int rec_depth, int max_depth);\n"
    return c_code


def generate_printers_files(
    output: str,
    all_files_resolve_structs: OrderedDict[str, StructInfo],
):
    printers_code = codegen.generate_code_for_structs(
        all_files_resolve_structs, generate_print_function
    )
    printers_headers = codegen.generate_code_for_structs(
        all_files_resolve_structs, generate_print_function_header
    )

    for struct_name, code in printers_code.items():
        deps = codegen.get_struct_dependencies(
            all_files_resolve_structs[struct_name], all_files_resolve_structs
        )
        with open(f"{output}/print_{struct_name}.c", "w") as f:
            for dep in deps:
                f.write(f'// depends on "print_{dep}.c"\n')
            f.write(typeassert.as_string(code))
        with open(f"{output}/print_{struct_name}.h", "w") as f:
            for dep in deps:
                f.write(f'// depends on "print_{dep}.h"\n')
            f.write(typeassert.as_string(printers_headers[struct_name]))
