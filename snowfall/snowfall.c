#include <godlib/gemdos/gemdos.h>
#include <godlib/graphic/graphic.h>
#include <godlib/font8x8/font8x8.h>
#include <godlib/ikbd/ikbd.h>
#include <godlib/platform/platform.h>
#include <godlib/memory/memory.h>
#include <godlib/vbl/vbl.h>
#include <godlib/video/video.h>
#include "assets/palette.h"
extern void Snow_Step(void);
extern U8 Snow_Background[];
U8 *gSnowScreen;
static sGraphicCanvas gSnowCanvas;
volatile U16 gSnowReady,gSnowExited,gSnowPaused,gSnowDensity=8,gSnowSingleStep;
volatile U32 gSnowSteps;
static U32 gRandom=0x12345678UL;
static U16 Snow_Random(void)
{
    gRandom^=gRandom<<13;gRandom^=gRandom>>17;gRandom^=gRandom<<5;
    return (U16)gRandom;
}
static void Box(S16 x,S16 y,S16 w,S16 h,U16 colour)
{
    sGraphicRect r;r.mX=x;r.mY=y;r.mWidth=w;r.mHeight=h;
    GraphicCanvas_DrawBox((&gSnowCanvas),&r,colour);
}
static void Prepare(void)
{
    sGraphicCanvas *c=(&gSnowCanvas);sGraphicPos p;U16 i;
    GraphicCanvas_CopyScreen(c,Snow_Background);
    Font8x8_PrintColourCanvas("GODLIB / SNOWFALL",c,96,4,7);
    Font8x8_PrintColourCanvas("SPACE PAUSE  S STEP  C CLEAR  ESC EXIT",c,16,16,4);
    /* A sparse initial shower, confined above all scenery. */
    for(i=0;i<120;++i) {
        p.mX=3+Snow_Random()%314;p.mY=27+Snow_Random()%26;
        GraphicCanvas_DrawPixel(c,&p,8);
    }
    gSnowSteps=0;
}
static void Emit(void)
{
    U16 i;sGraphicPos p;
    for(i=0;i<gSnowDensity;++i) {
        p.mX=3+Snow_Random()%314;p.mY=25;
        GraphicCanvas_DrawPixel((&gSnowCanvas),&p,8);
    }
}
static void Paint(void)
{
    S16 x=IKBD_GetMouseX(),y=IKBD_GetMouseY();
    if(x<4 || x>314 || y<32 || y>193)return;
    if(IKBD_GetMouseButtonLeft())Box(x-2,y-1,5,3,4);
    if(IKBD_GetMouseButtonRight())Box(x-2,y-1,5,3,0);
}
#ifdef SNOW_VERIFY
#include <godlib/memory/memory.h>
extern void Snow_Reference(void);
extern U16 Snow_Compare(void);
static U16 gReferenceStorage[16000];
U8 *gSnowReference=(U8*)gReferenceStorage;
volatile U32 gSnowChecks,gSnowMismatch;
static void Snow_Verify(void)
{
    U16 i;U8 *screen=gSnowScreen;
    for(i=0;i<1200;++i) {
        /* Test emission, dense piles, word seams and changing obstacles. */
        if(i==300)Box(64,85,192,3,4);
        if(i==600)Box(112,82,96,12,0);
        if(i==900)Box(12,54,292,3,4);
        gSnowDensity=(i<400)?8:16;Emit();
        Memory_Copy(32000UL,screen,gSnowReference);
        Snow_Step();gSnowScreen=gSnowReference;Snow_Reference();gSnowScreen=screen;
        if(Snow_Compare())++gSnowMismatch;
        ++gSnowChecks;
    }
    gSnowDensity=8;
}
#endif
S16 GodLib_Game_Main(S16 argc,char **argv)
{
    U16 quit=0;void *allocation;
    (void)argc;(void)argv;GemDos_Super(0);Platform_Init();
    Video_SetResolution(320,200,eGRAPHIC_COLOURMODE_4PLANE,320);
    allocation=mMEMSCREENCALLOC(32000UL+255UL);
    if(!allocation){Platform_DeInit();return 1;}
    gSnowScreen=(U8*)(((U32)allocation+255UL)&~255UL);
    GraphicCanvas_Init(&gSnowCanvas,eGRAPHIC_COLOURMODE_4PLANE,320,200);
    gSnowCanvas.mpVRAM=gSnowScreen;
    IKBD_EnableMouse();IKBD_SetMouseX(160);IKBD_SetMouseY(100);
    Prepare();
#ifdef SNOW_VERIFY
    Snow_Verify();Prepare();
#endif
    Video_SetPhysic((U16*)gSnowScreen);Video_SetPalST(gSnowPalette);
    Vbl_WaitVbl();gSnowReady=1;
    while(!quit) {
        Vbl_WaitVbl();IKBD_Update();
        while(IKBD_GetKbdBytesWaiting()) {
            U8 k=IKBD_PopKbdByte();
            if(k==eIKBDSCAN_ESC)quit=1;
            if(k==eIKBDSCAN_SPACE)gSnowPaused^=1;
            if(k==eIKBDSCAN_C)Prepare();
            if(k==eIKBDSCAN_S)gSnowSingleStep=1;
            if(k>=eIKBDSCAN_1 && k<=eIKBDSCAN_3)gSnowDensity=4<<(k-eIKBDSCAN_1);
        }
        Paint();
        if(!gSnowPaused || gSnowSingleStep) {
            Snow_Step();++gSnowSteps;
            if(!gSnowPaused)Emit();
            gSnowSingleStep=0;
        }

    }
    GraphicCanvas_DeInit(&gSnowCanvas);mMEMSCREENFREE(allocation);
    Platform_DeInit();gSnowExited=1;return 0;
}
