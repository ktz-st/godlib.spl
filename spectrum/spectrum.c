#include <godlib/gemdos/gemdos.h>
#include <godlib/graphic/graphic.h>
#include <godlib/ikbd/ikbd.h>
#include <godlib/memory/memory.h>
#include <godlib/mfp/mfp.h>
#include <godlib/platform/platform.h>
#include <godlib/screen/screen.h>
#include <godlib/system/system.h>
#include <godlib/vbl/vbl.h>
#include <godlib/video/video.h>
#include <stdio.h>
extern U8 Spectrum_Pixels[];
extern U16 Spectrum_PalST[],Spectrum_PalSTE[];
extern void Spectrum_TimerA(void),Spectrum_Hbl(void);
U16 * volatile gSpectrumFramePal;
volatile U16 gSpectrumReady,gSpectrumExited,gSpectrumEnabled=1;
volatile U16 gSpectrumSTE,gSpectrumMode,gSpectrumActive,gSpectrumFrameMode;
volatile U16 gSpectrumTimerCMask;
volatile U32 gSpectrumRasterFrames,gSpectrumVblFrames;
static void (*sVideoFunc)(void),(*sHbi)(void),(*sHblVector)(void);
static sMfpTimer sTimerA;
static U8 sTimerCMask;
static void Spectrum_Video(void)
{
    /* Start early enough for STOP/HBL + shifter hard sync before line zero. */
    volatile U8 *tacr=(volatile U8*)0xfffffa19UL;
    *tacr=0;
    gSpectrumActive=gSpectrumEnabled;
    gSpectrumFrameMode=gSpectrumSTE?gSpectrumMode:0;
    gSpectrumFramePal=gSpectrumFrameMode?Spectrum_PalSTE:Spectrum_PalST;
    gSpectrumTimerCMask=*(volatile U8*)0xfffffa15UL&0x20;
    if(gSpectrumActive) {
        *(volatile U8*)0xfffffa15UL&=(U8)~0x20;
        *(volatile U8*)0xfffffa1fUL=180;
        *tacr=4; /* /50: fire safely before the first visible line */
    }
    sVideoFunc();
    Video_SetPalST(gSpectrumFramePal);
    ++gSpectrumVblFrames;
}
static void Install(void)
{
    sMfpTimer timer;U16 iml=System_GetIML();System_SetIML(7);
    sVideoFunc=Vbl_GetpVbl()->mfVideoFunc;sHbi=Vbl_GetpVbl()->mfHbi;
    sHblVector=*(void(**)(void))0x68UL;
    Mfp_GetTimerA(&sTimerA);Memory_Clear(sizeof(timer),&timer);
    timer.mfTimerFunc=Spectrum_TimerA;timer.mMask=1;timer.mEnable=1;
    Mfp_InstallTimerA(&timer);
    sTimerCMask=*(volatile U8*)0xfffffa15UL&0x20;
    Vbl_GetpVbl()->mfHbi=0;
    *(void(**)(void))0x68UL=Spectrum_Hbl;
    Vbl_SetVideoFunc(Spectrum_Video);System_SetIML(iml);
}
static void Remove(void)
{
    U16 iml=System_GetIML();System_SetIML(7);
    *(volatile U8*)0xfffffa19UL=0;
    *(volatile U8*)0xfffffa0bUL&=(U8)~0x20;
    *(volatile U8*)0xfffffa0fUL&=(U8)~0x20;
    *(volatile U8*)0xfffffa15UL=(*(volatile U8*)0xfffffa15UL&(U8)~0x20)|sTimerCMask;
    Vbl_SetVideoFunc(sVideoFunc);Vbl_GetpVbl()->mfHbi=sHbi;
    *(void(**)(void))0x68UL=sHblVector;
    Mfp_InstallTimerA(&sTimerA);System_SetIML(iml);
}
S16 GodLib_Game_Main(S16 argc,char **argv)
{
    U16 quit=0,vdo;
    (void)argc;(void)argv;GemDos_Super(0);Platform_Init();vdo=System_GetVDO();
    if(vdo!=VDO_ST && vdo!=VDO_STE) {
        printf("Spectrum requires PAL ST/STE low resolution at 8 MHz.\n");
        Platform_DeInit();return 1;
    }
    gSpectrumSTE=vdo==VDO_STE;gSpectrumMode=gSpectrumSTE;
    Screen_Init(320,200,eGRAPHIC_COLOURMODE_4PLANE,0);
    if(!gScreenClass.mpMemBase){Platform_DeInit();return 1;}
    Memory_Copy(32000UL,Spectrum_Pixels,Screen_GetpLogic());
    Memory_Copy(32000UL,Spectrum_Pixels,Screen_GetpPhysic());
    Install();gSpectrumReady=1;
    while(!quit) {
        Screen_Update();IKBD_Update();
        while(IKBD_GetKbdBytesWaiting()) {
            U8 key=IKBD_PopKbdByte();
            if(key==eIKBDSCAN_ESC)quit=1;
            if(key==eIKBDSCAN_1)gSpectrumMode=0;
            if(key==eIKBDSCAN_2 && gSpectrumSTE)gSpectrumMode=1;
            if(key==eIKBDSCAN_SPACE)gSpectrumEnabled^=1;
        }
    }
    Remove();Screen_DeInit();Platform_DeInit();gSpectrumExited=1;return 0;
}
