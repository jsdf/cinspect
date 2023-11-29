from collections import OrderedDict
from collections import OrderedDict
from typing import Callable, Optional, OrderedDict, Set

from c_parser import StructInfo


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
