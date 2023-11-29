from collections import OrderedDict
from collections import OrderedDict
from typing import Callable, Optional, OrderedDict, Set

from c_parser import StructInfo


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


# imgui_templates = {
#     "int": lambda field_name: 'ImGui::InputInt("{field_name}", &data.{field_name});\n',
#     "short": lambda field_name: 'ImGui::InputInt("{field_name}", &data.{field_name});\n',
#     "long": lambda field_name: 'ImGui::InputInt("{field_name}", &data.{field_name});\n',
#     "unsigned int": lambda field_name: 'ImGui::InputInt("{field_name}", &data.{field_name});\n',
#     "unsigned short": lambda field_name: 'ImGui::InputInt("{field_name}", &data.{field_name});\n',
#     "unsigned long": lambda field_name: 'ImGui::InputInt("{field_name}", &data.{field_name});\n',
#     "signed": lambda field_name: 'ImGui::InputInt("{field_name}", &data.{field_name});\n',
#     "unsigned": lambda field_name: 'ImGui::InputInt("{field_name}", &data.{field_name});\n',
#     "float": lambda field_name: 'ImGui::InputFloat("{field_name}", &data.{field_name});\n',
#     "double": lambda field_name: 'ImGui::InputDouble("{field_name}", &data.{field_name});\n',
#     "cstring": lambda field_name: 'ImGui::InputText("{field_name}", data.{field_name}, sizeof(data.{field_name}));\n',
# }


def generate_imgui_render_editor_code(
    struct_info: StructInfo, all_structs: OrderedDict[str, StructInfo]
) -> str:
    imgui_code = f"// ImGui form for {struct_info.name}\n"
    imgui_code += (
        "void Show" + struct_info.name + "Editor(" + struct_info.name + "& data) {\n"
    )

    for field in struct_info.fields:
        if field.reference_depth > 0:
            # for simplicity, let's handle only non-pointer and non-reference fields.
            # you would need to add additional logic for pointers/references.
            imgui_code += f'    ImGui::Text("{field.name}: Array<{field.custom_type or field.type_handler}>");\n'
            continue

        if field.type_handler == "int":
            imgui_code += f'    ImGui::InputInt("{field.name}", &data.{field.name});\n'
        elif field.type_handler == "float":
            imgui_code += (
                f'    ImGui::InputFloat("{field.name}", &data.{field.name});\n'
            )
        elif field.type_handler == "bool":
            imgui_code += f'    ImGui::Checkbox("{field.name}", &data.{field.name});\n'
        elif field.type_handler == "struct" and field.custom_type in all_structs:
            # assumes you have also generated a Show...Editor function for each custom struct
            imgui_code += f"    Show{field.custom_type}Editor(data.{field.name});\n"
        else:
            imgui_code += f'    ImGui::Text("{field.name}: Unsupported Type");\n'
        # add other type_handler conditions here depending on your needs

    imgui_code += "}\n"

    return imgui_code


def generate_imgui_render_editor_code_header(
    struct_info: StructInfo, all_structs: OrderedDict[str, StructInfo]
) -> str:
    imgui_code = (
        "void Show" + struct_info.name + "Editor(" + struct_info.name + "& data);\n"
    )
    return imgui_code


def get_struct_dependencies(
    struct_info: StructInfo, all_structs: OrderedDict[str, StructInfo]
) -> Set[str]:
    """
    Get a list of all struct dependencies for a given struct info.
    """
    dependencies: Set[str] = set()
    for field in struct_info.fields:
        if field.type_handler == "struct" and field.custom_type in all_structs:
            dependencies.add(field.custom_type)
    return dependencies


def generate_code_for_struct(
    struct_info: StructInfo,
    all_structs: OrderedDict[str, StructInfo],
    code_fragments: OrderedDict[str, Optional[str]],
    generator: Callable[[StructInfo, OrderedDict[str, StructInfo]], str],
) -> OrderedDict[str, Optional[str]]:
    dependencies = get_struct_dependencies(struct_info, all_structs)
    for dependency in dependencies:
        if dependency not in code_fragments:
            # generate code for the dependency first
            code_fragments[dependency] = None  # placeholder to avoid infinite recursion
            code_fragments[dependency] = generator(all_structs[dependency], all_structs)
    if struct_info.name not in code_fragments:
        code_fragments[
            struct_info.name
        ] = None  # placeholder to avoid infinite recursion
        code_fragments[struct_info.name] = generator(
            struct_info,
            all_structs,
        )
    return code_fragments


def generate_code_for_structs(
    all_structs: OrderedDict[str, StructInfo],
    generator: Callable[[StructInfo, OrderedDict[str, StructInfo]], str],
) -> OrderedDict[str, Optional[str]]:
    code_fragments: OrderedDict[
        str, Optional[str]
    ] = OrderedDict()  # will be populated in dependency order

    for _struct_name, struct_info in all_structs.items():
        if struct_info.options.get("generate"):
            generate_code_for_struct(
                struct_info, all_structs, code_fragments, generator
            )
    return code_fragments
