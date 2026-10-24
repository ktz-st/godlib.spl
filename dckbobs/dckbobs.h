#ifndef DCKBOBS_H
#define DCKBOBS_H
#include <godlib/graphic/graphic.h>
#include <godlib/sprite/sprite.h>
extern const U16 Bobs_Palette[16],Bobs_Lengths[8];
extern const S16 *Bobs_Paths[8];
extern const sSprite Bobs_Sprites[3];
void Bobs_Init(void),Bobs_Advance(void),Bobs_Restore(void),Bobs_Draw(void),Bobs_Store(void),Bobs_Frame(void),Bobs_Seed(void);
extern sGraphicPos gBobsPositions[8],gBobsPrevious[8];
extern U16 gBobsIndices[8];
extern sGraphicChunkList gBobsChunks[2],*gBobsList;
extern sGraphicCanvas *gBobsCanvas,*gBobsBackCanvas;
extern void (*gBobsDrawFn)(sGraphicCanvas *,sGraphicPos *,void *);
extern volatile U16 gBobsCount,gBobsPath,gBobsTrails,gBobsPaused,gBobsBlitter,gBobsReady,gBobsExited,gBobsRaster;
extern volatile U32 gBobsFrames,gBobsMissedVbl;
#endif
