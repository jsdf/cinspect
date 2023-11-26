#ifndef CINSPECT_H_
#define CINSPECT_H_

#ifdef CINSPECT_ANALYZE
#define CINSPECT() _Pragma("generate_cinspect")
#define CINSPECT_STRUCT __attribute__((annotate("generate_cinspect")))
#else
#define CINSPECT() ;
#define CINSPECT_STRUCT
#endif

#endif // CINSPECT_H_