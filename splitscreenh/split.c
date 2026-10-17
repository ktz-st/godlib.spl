/* Top-HUD split adapted from PacMad STE, with horizontal fine scroll.
 * Timer B is rearmed by GodLib's VBL handler, never by the game loop. */
#include <godlib/memory/memory.h>
#include <godlib/mfp/mfp.h>
#include <godlib/system/system.h>
#include <godlib/vbl/vbl.h>
#include "split.h"
#include <godlib/video/video.h>
extern U16 gHSplitHudPalette[16];
volatile U32 gHSplitPanel,gHSplitTerrain;
volatile U16 gHSplitFine,gHSplitLineWords;
volatile U16 gHSplitTimerCMask,gHSplitHasBlitter;
volatile U8 gHSplitReload=14;
extern void HSplit_TimerB(void);
extern void HSplit_SetHud(const void *panel);
static void (*sVideoFunc)(void),(*sTimerFunc)(void);
static U8 sTimerLine,sInstalled;
static sMfpTimer sTimer;
static void HSplit_Video(void)
{
    /* Defer TOS Timer C (IPL 6) so it cannot delay this raster boundary. */
    gHSplitTimerCMask=*(volatile U8*)0xfffffa15UL & 0x20;
    *(volatile U8*)0xfffffa15UL &= (U8)~0x20;
    sVideoFunc();
    /* The queued address and hardware scroll belong to the same video update.
     * Do not read the main loop's X: it may already describe the next frame. */
    gHSplitTerrain=(U32)Video_GetpPhysic();
    gHSplitFine=*(volatile U8*)0xffff8265UL & 15;
    gHSplitLineWords=80-(gHSplitFine?4:0);
    HSplit_SetHud((void*)gHSplitPanel);
    Video_SetPalST(gHSplitHudPalette);
}
void HSplit_Init(void *panel)
{
    sMfpTimer timer;U16 iml=System_GetIML();
    System_SetIML(7);
    gHSplitPanel=(U32)panel;
    gHSplitHasBlitter=System_GetBLT()==BLT_BLITTER;
    sVideoFunc=Vbl_GetpVbl()->mfVideoFunc;
    sTimerFunc=Vbl_GetpVbl()->mfTimerBFunc;
    sTimerLine=Vbl_GetpVbl()->mTimerBScanLine;
    Mfp_GetTimerB(&sTimer);
    Memory_Clear(sizeof(timer),&timer);
    timer.mfTimerFunc=HSplit_TimerB;timer.mData=gHSplitReload;
    timer.mMask=1;timer.mEnable=1;
    Vbl_InstallTimerB(&timer);
    Vbl_SetVideoFunc(HSplit_Video);
    sInstalled=1;
    System_SetIML(iml);
}
void HSplit_DeInit(void)
{
    U16 iml;
    if(!sInstalled)return;
    iml=System_GetIML();System_SetIML(7);
    *(volatile U8*)0xfffffa1bUL=0;
    *(volatile U8*)0xfffffa0bUL &= (U8)~1; /* clear pending Timer B */
    *(volatile U8*)0xfffffa0fUL &= (U8)~1; /* clear in-service bit */
    *(volatile U8*)0xfffffa15UL |= (U8)gHSplitTimerCMask;
    Vbl_SetVideoFunc(sVideoFunc);
    Vbl_GetpVbl()->mfTimerBFunc=sTimerFunc;
    Vbl_GetpVbl()->mTimerBScanLine=sTimerLine;
    Mfp_InstallTimerB(&sTimer);
    sInstalled=0;
    System_SetIML(iml);
}
