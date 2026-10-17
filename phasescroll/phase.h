#ifndef PHASE_H
#define PHASE_H
#include <godlib/base/base.h>
/* Original assembler state, 2-byte packed GCC ELF layout. */
typedef struct { U8 *buffer,*screen; S16 x,speed,dir,fill,coarse,mapx,previous,y,mapy; } sPhase;
extern sPhase Phase_State;
extern U8 *Phase_Tiles,Phase_TileAsset[],Phase_Map[];
extern U16 Phase_Palette[];
void Phase_Init(void);
void Phase_Step(void);
void HSplit_Init(void *panel);
void HSplit_DeInit(void);
#endif
