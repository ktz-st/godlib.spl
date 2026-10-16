#ifndef PALSPLIT_H
#define PALSPLIT_H
#include <godlib/base/base.h>
extern U16 gPalSplitGrey[16];
extern volatile U16 gPalSplitEnabled;
void PalSplit_Init(void);
void PalSplit_DeInit(void);
#endif
