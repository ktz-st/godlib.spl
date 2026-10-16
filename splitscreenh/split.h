#ifndef HSPLIT_H
#define HSPLIT_H
#include <godlib/base/base.h>
/* STE low-res PAL, 16-row HUD at stride 160, then 184 terrain rows at stride 320. */
void HSplit_Init(void *panel);
void HSplit_DeInit(void);
#endif
