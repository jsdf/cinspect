#include "../cinspect.h"

typedef struct Thang
{
    int someInt;
} CINSPECT_STRUCT Thang;

typedef struct PhysBody
{
    float mass;
} PhysBody;

typedef struct GameObject
{
    Thang **physBody;
    Thang child;
} CINSPECT_STRUCT GameObject;