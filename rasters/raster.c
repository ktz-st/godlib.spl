/* Raster list: same VBL/Timer B installation as the split screen demo.
 * Timer B is rearmed by GodLib's VBL handler, never by the game loop. */
#include <godlib/memory/memory.h>
#include <godlib/mfp/mfp.h>
#include <godlib/system/system.h>
#include <godlib/vbl/vbl.h>
#include "rasters.h"
#include <godlib/video/video.h>

volatile U16 gRasterEnabled=1,gRasterActive;
U16 gRasterAnimate=1,gRasterSpeed=1,gRasterPhase,gRasterFramePhase;
U16 gRasterLut[64];
U16 gRasterPalette[16]={0x012,0x111,0x222,0x333,0x444,0x555,0x666,0x777,
                      0x700,0x070,0x007,0x770,0x707,0x077,0x555,0x777};
sRasterStep gRasterSteps[49];
sRasterStep * volatile gRasterNext;
volatile U16 gRasterRemaining;
volatile U16 gRasterTimerCMask;
volatile U8 gRasterReload=3;
extern void Raster_TimerB(void);
static void (*sVideoFunc)(void),(*sTimerFunc)(void);
static U8 sTimerLine,sInstalled;
static sMfpTimer sTimer;
static void Raster_Video(void)
{
    /* Defer TOS Timer C (IPL 6) so it cannot delay this raster boundary. */
    gRasterTimerCMask=*(volatile U8*)0xfffffa15UL & 0x20;
    *(volatile U8*)0xfffffa15UL &= (U8)~0x20;
    sVideoFunc();
    {
        U16 i;
        gRasterActive=gRasterEnabled;
        if(gRasterAnimate)gRasterPhase=(gRasterPhase+gRasterSpeed)&63;
        gRasterFramePhase=gRasterPhase;
        gRasterPalette[0]=gRasterActive?gRasterLut[gRasterFramePhase]:0x012;
        for(i=0;i<49;++i) {
            gRasterSteps[i].mDelay=3;gRasterSteps[i].mPad=0;
            gRasterSteps[i].mColour=gRasterLut[(i+1+gRasterFramePhase)&63];
        }
        gRasterNext=gRasterSteps;gRasterRemaining=49;
        Video_SetPalST(gRasterPalette);
    }
}
void Raster_Init(void)
{
    sMfpTimer timer;U16 iml=System_GetIML();
    System_SetIML(7);
    sVideoFunc=Vbl_GetpVbl()->mfVideoFunc;
    sTimerFunc=Vbl_GetpVbl()->mfTimerBFunc;
    sTimerLine=Vbl_GetpVbl()->mTimerBScanLine;
    Mfp_GetTimerB(&sTimer);
    Memory_Clear(sizeof(timer),&timer);
    timer.mfTimerFunc=Raster_TimerB;timer.mData=gRasterReload;
    timer.mMask=1;timer.mEnable=1;
    Vbl_InstallTimerB(&timer);
    Vbl_SetVideoFunc(Raster_Video);
    sInstalled=1;
    System_SetIML(iml);
}
void Raster_DeInit(void)
{
    U16 iml;
    if(!sInstalled)return;
    iml=System_GetIML();System_SetIML(7);
    *(volatile U8*)0xfffffa1bUL=0;
    *(volatile U8*)0xfffffa0bUL &= (U8)~1; /* clear pending Timer B */
    *(volatile U8*)0xfffffa0fUL &= (U8)~1; /* clear in-service bit */
    *(volatile U8*)0xfffffa15UL |= (U8)gRasterTimerCMask;
    Vbl_SetVideoFunc(sVideoFunc);
    Vbl_GetpVbl()->mfTimerBFunc=sTimerFunc;
    Vbl_GetpVbl()->mTimerBScanLine=sTimerLine;
    Mfp_InstallTimerB(&sTimer);
    sInstalled=0;
    System_SetIML(iml);
}
