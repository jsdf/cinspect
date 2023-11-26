#include "../struct_reflect.h"

StructFieldInfo test_output_Vec3dFields[] = {
    {
        .name = "x",
        .type = TYPE_FLOAT,
    },
    {
        .name = "y",
        .type = TYPE_FLOAT,
    },
    {
        .name = "z",
        .type = TYPE_FLOAT,
    }};

StructInfo test_output_Vec3d = {
    .name = "Vec3d",
    .fields =
        test_output_Vec3dFields,
    .num_fields = struct_reflect_c_array_len(test_output_Vec3dFields)};

StructFieldInfo test_output_GameObjectFields[] = {
    {
        .name = "id",
        .type = TYPE_INT,
    },
    {
        .name = "position",
        .type = TYPE_STRUCT,
        .struct_desc = &test_output_Vec3d,
    }};

StructInfo test_output_GameObject = {
    .name = "GameObject",
    .fields = test_output_GameObjectFields,
    .num_fields = struct_reflect_c_array_len(test_output_GameObjectFields)};
