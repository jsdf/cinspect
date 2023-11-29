from collections import OrderedDict

import typeassert
from c_parser import StructInfo
import codegen


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


def generate_imgui_files(
    output: str,
    all_files_resolve_structs: OrderedDict[str, StructInfo],
):
    imgui_code = codegen.generate_code_for_structs(
        all_files_resolve_structs, generate_imgui_render_editor_code
    )
    imgui_headers = codegen.generate_code_for_structs(
        all_files_resolve_structs, generate_imgui_render_editor_code_header
    )
    for struct_name, code in imgui_code.items():
        deps = codegen.get_struct_dependencies(
            all_files_resolve_structs[struct_name], all_files_resolve_structs
        )
        with open(f"{output}/imgui_{struct_name}.cpp", "w") as f:
            for dep in deps:
                f.write(f'// depends on "imgui_{dep}.cpp"\n')
            f.write(typeassert.as_string(code))
        with open(f"{output}/imgui_{struct_name}.h", "w") as f:
            for dep in deps:
                f.write(f'// depends on "imgui_{dep}.h"\n')
            f.write(typeassert.as_string(imgui_headers[struct_name]))
