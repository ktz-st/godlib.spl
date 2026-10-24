#ifndef DCKWAVE_H
#define DCKWAVE_H
#include <godlib/base/base.h>
extern const U8 Dw_Picture[],Dw_Shifts[],Dw_Zero[];
extern const U16 Dw_Palette[],Dw_Masks[];
void Dw_Select(void);
void Dw_Frame(void);
void Dw_Draw(void);
void Dw_Show(void);
#endif
