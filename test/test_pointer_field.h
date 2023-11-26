#include "cinspect.h"

typedef struct Thing
{
    int someInt;
} Thing;

CINSPECT();
typedef struct PhysBody
{
    float mass;
} PhysBody;

CINSPECT();
typedef struct GameObject
{
    Thing **physBody;
    Thing child;
} GameObject;