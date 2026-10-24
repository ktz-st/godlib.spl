#ifndef EXAMPLE_DCK_MOD_VIS_H
#define EXAMPLE_DCK_MOD_VIS_H
#include <godlib/base/base.h>
/* screen, normalized activity levels 0..16, four previous levels for this page. */
typedef void (*fDckModVisDraw)(void *,const U16 *,U16 *);
extern fDckModVisDraw gDckModVisDraw[5];
extern U16 gDckModVisPalette[16];
#endif
