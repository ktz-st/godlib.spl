#ifndef SPLIT_H
#define SPLIT_H
#include <godlib/base/base.h>
/* STE low-res PAL, identical 160-byte strides in terrain and panel. */
void Split_Init(void *panel);
void Split_DeInit(void);
#endif
