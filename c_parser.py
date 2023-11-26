# pyright: reportMissingTypeStubs=false, reportUnknownMemberType=false

from collections import OrderedDict
from typing import Dict, List, Set, Optional, Any, NamedTuple
import clang.cindex
import typeassert


# name: name of the field
class UnresolvedFieldInfo(NamedTuple):
    name: str
    typename: str
    reference_depth: int
    location: clang.cindex.SourceLocation


class UnresolvedStructInfo(NamedTuple):
    name: str
    fields: List[UnresolvedFieldInfo]
    options: Dict[str, Any]
    location: clang.cindex.SourceLocation


class FieldInfo(NamedTuple):
    name: str
    type_handler: Optional[str]
    custom_type: Optional[str]
    reference_depth: int
    location: clang.cindex.SourceLocation


class StructInfo(NamedTuple):
    name: str
    fields: List[FieldInfo]
    options: Dict[str, Any]
    location: clang.cindex.SourceLocation


debug_print_enabled = True


def dbg(*args: Any, **kwargs: Any) -> None:
    if debug_print_enabled:
        print(*args, **kwargs)


primitive_types: Set[str] = {
    "char",
    "cstring",  # special case for char*
    "short",
    "int",
    "long",
    "float",
    "double",
    "signed",
    "unsigned",
    "void",
    "unsigned int",
    "unsigned long",
    "unsigned short",
}


def get_ast(filename: str) -> clang.cindex.TranslationUnit:
    index = clang.cindex.Index.create()
    translation_unit = index.parse(
        filename,
        args=[
            "-x",
            "c++",
            "-DCINSPECT_ANALYZE=1",
        ],
    )

    # Check if there are any diagnostics (errors or warnings)
    if translation_unit.diagnostics:
        for diag in translation_unit.diagnostics:
            print(f"Severity: {diag.severity}")
            print(f"Location: {diag.location}")
            print(f"Message: {diag.spelling}\n")
        if translation_unit.diagnostics[0].severity > 2:
            raise Exception("Failed to parse file '" + filename + "'")

    return translation_unit


def dbg_print_ast_node(node: clang.cindex.Cursor, depth: int = 0):
    """
    Recursively prints the AST nodes.
    Args:
        node: The AST node to print.
        depth: The current depth in the tree (used for indentation).
    """
    # Indentation for readability
    indent = "  " * depth
    dbg(
        f"{indent}{node.kind} ({node.spelling}, {node.location.line}:{node.location.column})"
    )

    # Recursively print children nodes
    for child in node.get_children():
        dbg_print_ast_node(typeassert.as_cursor(child), depth + 1)


def get_pointer_info(cursor: clang.cindex.Cursor) -> tuple[int, clang.cindex.Type]:
    """
    Gets the number of pointer levels and the ultimate type being pointed to.
    Args:
        cursor: clang.cindex.Cursor for a field declaration
    Returns:
        tuple: A tuple containing the number of pointer levels and the ultimate type
    """
    count = 0
    cursor_type = typeassert.as_type(cursor.type)
    while cursor_type.kind == clang.cindex.TypeKind.POINTER:  # type: ignore
        count += 1
        cursor_type = typeassert.as_type(cursor_type.get_pointee())

    # The ultimate type pointed to (after resolving all pointers)
    ultimate_type = cursor_type
    return count, ultimate_type


def visit_struct_decl(
    node: clang.cindex.Cursor,
    types: List[UnresolvedStructInfo],
) -> None:
    dbg("visit_struct_decl")
    struct_name = typeassert.as_string(node.spelling or node.displayname)
    dbg("struct_name:", struct_name)
    # pretty print ast node

    dbg_print_ast_node(node)

    fields: List[UnresolvedFieldInfo] = []
    attributes = [
        typeassert.as_string(c.spelling or c.displayname)
        for c in node.get_children()
        if c.kind == clang.cindex.CursorKind.ANNOTATE_ATTR
    ]

    options = pragmas_to_options(attributes)

    for c in node.get_children():
        if c.kind == clang.cindex.CursorKind.FIELD_DECL:  # type: ignore
            field_name: str = typeassert.as_string(c.spelling or c.displayname)
            dbg("visiting field: ", field_name)
            dbg("field type spelling: ", c.type.spelling)
            dbg("ast node: ")
            dbg_print_ast_node(c)

            reference_depth, ultimate_type = get_pointer_info(c)
            typename = typeassert.as_string(ultimate_type.spelling)

            dbg("typename: ", typename)
            dbg("reference_depth: ", reference_depth)

            fields.append(
                UnresolvedFieldInfo(
                    field_name,
                    typename,
                    reference_depth,
                    typeassert.as_location(c.location),
                )
            )

    types.append(
        UnresolvedStructInfo(
            struct_name, fields, options, typeassert.as_location(node.location)
        )
    )


def pragmas_to_options(pragmas: List[str]) -> Dict[str, Any]:
    options: Dict[str, Any] = {}
    for pragma in pragmas:
        if pragma == "generate_cinspect":
            options["generate"] = True
    return options


def find_struct_attributes(cursor: clang.cindex.Cursor) -> List[str]:
    """
    Finds attributes of a struct declaration.
    Args:
        cursor: Cursor pointing to the struct declaration.
    Returns:
        A list of attributes applied to the struct.
    """
    attributes: List[str] = []
    in_attribute = False
    current_attribute: str = ""

    for token in cursor.get_tokens():
        dbg("token: ", token.spelling)
        # Detect the start of an attribute
        if token.spelling == "__attribute__":
            in_attribute = True
            current_attribute = token.spelling
            continue

        # Accumulate tokens that are part of the attribute
        if in_attribute:
            current_attribute += " " + typeassert.as_string(token.spelling)
            # Detect the end of the attribute
            if token.spelling.endswith(")"):
                attributes.append(current_attribute)
                in_attribute = False
                current_attribute = ""

    return attributes


def extract_types(ast: clang.cindex.TranslationUnit) -> List[UnresolvedStructInfo]:
    types: List[UnresolvedStructInfo] = []
    cur_pragmas: List[str] = []

    for node_untyped in ast.cursor.get_children():
        node = typeassert.as_cursor(node_untyped)
        dbg("visiting node: ", node.kind)
        dbg_print_ast_node(node)

        # note: clang eliminates the #pragma directives from the AST
        # so this code is probably going away
        if node.kind == clang.cindex.CursorKind.PREPROCESSING_DIRECTIVE:  # type: ignore
            cur_pragmas.append(typeassert.as_string(node.spelling))
            print("pragma: ", node.spelling)
            continue

        if node.kind == clang.cindex.CursorKind.TYPEDEF_DECL:  # type: ignore
            if node.type.kind == clang.cindex.TypeKind.RECORD:  # type: ignore
                if node.type.get_children() is None:
                    continue
                visit_struct_decl(
                    typeassert.as_cursor(node.type),
                    types,
                )
        elif node.kind == clang.cindex.CursorKind.STRUCT_DECL:  # type: ignore
            visit_struct_decl(
                typeassert.as_cursor(node),
                types,
            )
        cur_pragmas = []

    return types


def resolve_structs(ast: clang.cindex.TranslationUnit) -> OrderedDict[str, StructInfo]:
    types = extract_types(ast)

    types_by_name: Dict[str, UnresolvedStructInfo] = {t.name: t for t in types}
    resolved_structs: OrderedDict[str, StructInfo] = OrderedDict()
    for t in types:
        resolved_fields: List[FieldInfo] = []
        for f in t.fields:
            type_handler: Optional[str] = None
            custom_type: Optional[str] = None
            if f.typename in primitive_types:
                type_handler = f.typename
            elif f.typename in types_by_name:
                type_handler = "struct"
                custom_type = f.typename
            resolved_fields.append(
                FieldInfo(
                    f.name, type_handler, custom_type, f.reference_depth, f.location
                )
            )
        resolved_structs[t.name] = StructInfo(
            t.name, resolved_fields, t.options, t.location
        )
    return resolved_structs
