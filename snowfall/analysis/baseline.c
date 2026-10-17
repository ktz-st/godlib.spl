/* Preserved pre-optimization benchmark, not linked into SNOW.PRG. */
#include <godlib/gemdos/gemdos.h>
#include <godlib/graphic/graphic.h>
#include <godlib/font8x8/font8x8.h>
#include <godlib/ikbd/ikbd.h>
#include <godlib/platform/platform.h>
#include <godlib/memory/memory.h>
#include <godlib/screen/screen.h>
#include <godlib/video/video.h>
#include "assets/palette.h"
extern void Snow_Step(void);
extern U8 Snow_Background[];
U8 *gSnowScreen;

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
    GraphicCanvas_DrawBox(Screen_GetpBackGraphic(),&r,colour);
}
static void Prepare(void)
{
    sGraphicCanvas *c=Screen_GetpBackGraphic();sGraphicPos p;U16 i;
    GraphicCanvas_CopyScreen(c,Snow_Background);
    Font8x8_PrintColourCanvas("GODLIB / SNOWFALL",c,96,4,7);
    Font8x8_PrintColourCanvas("SPACE PAUSE  S STEP  C CLEAR  ESC EXIT",c,16,16,4);
    /* A sparse initial shower, confined above all scenery. */
    for(i=0;i<120;++i) {
        p.mX=3+Snow_Random()%314;p.mY=27+Snow_Random()%26;
        GraphicCanvas_DrawPixel(c,&p,8);
    }
    gSnowScreen=(U8*)Screen_GetpBack();gSnowSteps=0;
}
static void Emit(void)
{
    U16 i;sGraphicPos p;
    for(i=0;i<gSnowDensity;++i) {
        p.mX=3+Snow_Random()%314;p.mY=25;
        GraphicCanvas_DrawPixel(Screen_GetpBackGraphic(),&p,8);
    }
}
static void Paint(void)
{
    S16 x=IKBD_GetMouseX(),y=IKBD_GetMouseY();
    if(x<4 || x>314 || y<32 || y>193)return;
    if(IKBD_GetMouseButtonLeft())Box(x-2,y-1,5,3,4);
    if(IKBD_GetMouseButtonRight())Box(x-2,y-1,5,3,0);
}
S16 GodLib_Game_Main(S16 argc,char **argv)
{
    U16 quit=0;
    (void)argc;(void)argv;GemDos_Super(0);Platform_Init();
    Screen_Init(320,200,eGRAPHIC_COLOURMODE_4PLANE,0);
    if(!gScreenClass.mpMemBase){Platform_DeInit();return 1;}
    IKBD_EnableMouse();IKBD_SetMouseX(160);IKBD_SetMouseY(100);
    Prepare();Video_SetPalST(gSnowPalette);gSnowReady=1;
    while(!quit) {
        Screen_Update();IKBD_Update();
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
        GraphicCanvas_CopyScreen(Screen_GetpLogicGraphic(),Screen_GetpBack());
    }
    Screen_DeInit();Platform_DeInit();gSnowExited=1;return 0;
}
