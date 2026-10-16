/* Bottom-panel split adapted from River Raid STE, itself based on PacMad STE.
 * Timer B is rearmed by GodLib's VBL handler, never by the game loop. */
#include <godlib/memory/memory.h>
#include <godlib/mfp/mfp.h>
#include <godlib/system/system.h>
#include <godlib/vbl/vbl.h>
#include "split.h"
volatile U32 gSplitPanel;
volatile U16 gSplitTimerCMask,gSplitHasBlitter;
volatile U8 gSplitReload=159;
extern void Split_TimerB(void);
static void (*sVideoFunc)(void),(*sTimerFunc)(void);
static U8 sTimerLine,sInstalled;
static sMfpTimer sTimer;
static void Split_Video(void)
{
    /* Defer TOS Timer C (IPL 6) so it cannot delay this raster boundary. */
    gSplitTimerCMask=*(volatile U8*)0xfffffa15UL & 0x20;
    *(volatile U8*)0xfffffa15UL &= (U8)~0x20;
    sVideoFunc();
}
void Split_Init(void *panel)
{
    sMfpTimer timer;U16 iml=System_GetIML();
    System_SetIML(7);
    gSplitPanel=(U32)panel;
    gSplitHasBlitter=System_GetBLT()==BLT_BLITTER;
    sVideoFunc=Vbl_GetpVbl()->mfVideoFunc;
    sTimerFunc=Vbl_GetpVbl()->mfTimerBFunc;
    sTimerLine=Vbl_GetpVbl()->mTimerBScanLine;
    Mfp_GetTimerB(&sTimer);
    Memory_Clear(sizeof(timer),&timer);
    timer.mfTimerFunc=Split_TimerB;timer.mData=gSplitReload;
    timer.mMask=1;timer.mEnable=1;
    Vbl_InstallTimerB(&timer);
    Vbl_SetVideoFunc(Split_Video);
    sInstalled=1;
    System_SetIML(iml);
}
void Split_DeInit(void)
{
    U16 iml;
    if(!sInstalled)return;
    iml=System_GetIML();System_SetIML(7);
    *(volatile U8*)0xfffffa1bUL=0;
    *(volatile U8*)0xfffffa0bUL &= (U8)~1; /* clear pending Timer B */
    *(volatile U8*)0xfffffa0fUL &= (U8)~1; /* clear in-service bit */
    *(volatile U8*)0xfffffa15UL |= (U8)gSplitTimerCMask;
    Vbl_SetVideoFunc(sVideoFunc);
    Vbl_GetpVbl()->mfTimerBFunc=sTimerFunc;
    Vbl_GetpVbl()->mTimerBScanLine=sTimerLine;
    Mfp_InstallTimerB(&sTimer);
    sInstalled=0;
    System_SetIML(iml);
}
