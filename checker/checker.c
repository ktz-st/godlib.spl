#include <godlib/gemdos/gemdos.h>
#include <godlib/graphic/graphic.h>
#include <godlib/font8x8/font8x8.h>
#include <godlib/ikbd/ikbd.h>
#include <godlib/platform/platform.h>
#include <godlib/screen/screen.h>
#include <godlib/vbl/vbl.h>
#include <godlib/video/video.h>
extern const U8 Checker_Spans[];
extern const U32 Checker_Offsets[128];
extern void Checker_Draw(void);
extern void Tiny_RasterSync(void *screen);
const U8 *gCheckerCommands;
U8 *gCheckerScreen;
volatile U16 gCheckerPhase,gCheckerFramePhase,gCheckerPaused,gCheckerRaster;
volatile U16 gCheckerReady,gCheckerExited,gCheckerSpeed=1;
volatile S16 gCheckerDirection=1;
volatile U32 gCheckerFrames,gCheckerLastVbl,gCheckerMissedVbl;
static void PrepareScreen(void)
{
    static U16 pal[16]={0x001,0x777,0x012,0x123,0x123,0x345,0x234,0x567,
                               0x345,0x677,0x456,0x777,0x777,0x777,0x777,0x777};
    U16 y;sGraphicRect r={0,56,320,1};sGraphicCanvas *c=Screen_GetpBackGraphic();
    GraphicCanvas_ClearScreen(c);
    Font8x8_PrintColourCanvas("GODLIB / ROTATING CHECKERBOARD",c,40,16,1);
    Font8x8_PrintColourCanvas("SPACE PAUSE   1/2/3 SPEED",c,64,176,1);
    Font8x8_PrintColourCanvas("D REVERSE   R CPU   ESC EXIT",c,48,192,1);
    for(y=0;y<96;++y){r.mY=56+y;GraphicCanvas_DrawBox(c,&r,2+2*(y/24));}
    GraphicCanvas_CopyScreen(Screen_GetpLogicGraphic(),Screen_GetpBack());
    GraphicCanvas_CopyScreen(Screen_GetpPhysicGraphic(),Screen_GetpBack());Video_SetPalST(pal);
}
S16 GodLib_Game_Main(S16 argc,char **argv)
{
    U16 quit=0;(void)argc;(void)argv;GemDos_Super(0);Platform_Init();
    Screen_Init(320,200,eGRAPHIC_COLOURMODE_4PLANE,0);
    if(!gScreenClass.mpMemBase){Platform_DeInit();return 1;}
    PrepareScreen();gCheckerReady=1;
    while(!quit) {
        U32 now;Screen_Update();now=Vbl_GetCounter();
        if(gCheckerFrames && now-gCheckerLastVbl>1)gCheckerMissedVbl+=now-gCheckerLastVbl-1;
        gCheckerLastVbl=now;IKBD_Update();
        while(IKBD_GetKbdBytesWaiting()) {
            U8 k=IKBD_PopKbdByte();
            if(k==eIKBDSCAN_ESC)quit=1;
            if(k==eIKBDSCAN_SPACE)gCheckerPaused^=1;
            if(k==eIKBDSCAN_R)gCheckerRaster^=1;
            if(k==eIKBDSCAN_D)gCheckerDirection=-gCheckerDirection;
            if(k>=eIKBDSCAN_1 && k<=eIKBDSCAN_3)gCheckerSpeed=1<<(k-eIKBDSCAN_1);
        }
        if(!gCheckerPaused)gCheckerPhase=(gCheckerPhase+gCheckerDirection*gCheckerSpeed)&127;
        gCheckerFramePhase=gCheckerPhase;gCheckerScreen=(U8*)Screen_GetpLogic();
        if(gCheckerRaster){Tiny_RasterSync(Screen_GetpPhysic());*(volatile U16*)0xffff8240UL=0x070;}
        gCheckerCommands=Checker_Spans+Checker_Offsets[gCheckerPhase];Checker_Draw();
        if(gCheckerRaster)*(volatile U16*)0xffff8240UL=0x001;
        ++gCheckerFrames;
    }
    Screen_DeInit();Platform_DeInit();gCheckerExited=1;return 0;
}
