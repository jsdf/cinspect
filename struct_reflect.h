#ifndef STRUCT_REFLECT_H_
#define STRUCT_REFLECT_H_

#include <stddef.h>

typedef enum
{
    TYPE_INT,
    TYPE_LONG,
    TYPE_SHORT,
    TYPE_FLOAT,
    TYPE_DOUBLE,
    TYPE_CSTRING,
    TYPE_STRUCT,
    TYPE_ENUM,
} StructFieldType;

typedef struct StructFieldInfo
{
    const char *name;
    StructFieldType type;
    const struct StructInfo *struct_desc; // for TYPE_STRUCT
} StructFieldInfo;

typedef struct StructInfo
{
    const char *name;
    const StructFieldInfo *fields;
    size_t num_fields;
} StructInfo;

#define struct_reflect_c_array_len(V) (sizeof(V) / sizeof((V)[0]))

#endif // STRUCT_REFLECT_H_