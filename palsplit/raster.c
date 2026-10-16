/* Palette split: the same VBL/Timer B installation as the screen split demo.
 * Timer B is rearmed by GodLib's VBL handler, never by the game loop. */
#include <godlib/memory/memory.h>
#include <godlib/mfp/mfp.h>
#include <godlib/system/system.h>
#include <godlib/vbl/vbl.h>
#include "palsplit.h"
#include <godlib/video/video.h>
extern U16 gPalSplitPicture[];
volatile U16 gPalSplitEnabled=1,gPalSplitActive;
U16 gPalSplitGrey[16];
volatile U16 gPalSplitTimerCMask;
volatile U8 gPalSplitReload=99;
extern void PalSplit_TimerB(void);
static void (*sVideoFunc)(void),(*sTimerFunc)(void);
static U8 sTimerLine,sInstalled;
static sMfpTimer sTimer;
static void PalSplit_Video(void)
{
    /* Defer TOS Timer C (IPL 6) so it cannot delay this raster boundary. */
    gPalSplitTimerCMask=*(volatile U8*)0xfffffa15UL & 0x20;
    *(volatile U8*)0xfffffa15UL &= (U8)~0x20;
    sVideoFunc();
    Video_SetPalST(gPalSplitPicture+1);
    gPalSplitActive=gPalSplitEnabled;
}
void PalSplit_Init(void)
{
    sMfpTimer timer;U16 iml=System_GetIML();
    System_SetIML(7);
    sVideoFunc=Vbl_GetpVbl()->mfVideoFunc;
    sTimerFunc=Vbl_GetpVbl()->mfTimerBFunc;
    sTimerLine=Vbl_GetpVbl()->mTimerBScanLine;
    Mfp_GetTimerB(&sTimer);
    Memory_Clear(sizeof(timer),&timer);
    timer.mfTimerFunc=PalSplit_TimerB;timer.mData=gPalSplitReload;
    timer.mMask=1;timer.mEnable=1;
    Vbl_InstallTimerB(&timer);
    Vbl_SetVideoFunc(PalSplit_Video);
    sInstalled=1;
    System_SetIML(iml);
}
void PalSplit_DeInit(void)
{
    U16 iml;
    if(!sInstalled)return;
    iml=System_GetIML();System_SetIML(7);
    *(volatile U8*)0xfffffa1bUL=0;
    *(volatile U8*)0xfffffa0bUL &= (U8)~1; /* clear pending Timer B */
    *(volatile U8*)0xfffffa0fUL &= (U8)~1; /* clear in-service bit */
    *(volatile U8*)0xfffffa15UL |= (U8)gPalSplitTimerCMask;
    Vbl_SetVideoFunc(sVideoFunc);
    Vbl_GetpVbl()->mfTimerBFunc=sTimerFunc;
    Vbl_GetpVbl()->mTimerBScanLine=sTimerLine;
    Mfp_InstallTimerB(&sTimer);
    sInstalled=0;
    System_SetIML(iml);
}
