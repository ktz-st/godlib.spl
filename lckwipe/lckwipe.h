#ifndef LCKWIPE_H
#define LCKWIPE_H
#include <godlib/base/base.h>
extern const U8 Lw_Picture0[],Lw_Picture1[];
enum {LW_EFFECT_COUNT=11,LW_COLOURS=5};
extern const U16 Lw_Palette0[16],Lw_Palette1[16],Lw_Stages0[],Lw_Stages1[];
extern const U16 Lw_Limits[LW_EFFECT_COUNT],Lw_Speeds[LW_EFFECT_COUNT];
extern U8 *gLwDest;
extern const U8 *gLwSource;
extern S16 *gLwRows;
extern U16 *gLwOld;
extern U16 gLwPrevious[2];
extern S16 gLwRowHistory[2][160];
extern volatile U16 gLwEffect,gLwTarget,gLwClosing,gLwPhase,gLwImage,gLwPaused,gLwRaster,gLwReady,gLwExited;
extern volatile U32 gLwFrames,gLwMissedVbl,gLwSwaps;
void Lw_Begin(void),Lw_Render(void),Lw_Show(void);
#endif
