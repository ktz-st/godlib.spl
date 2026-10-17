#include <godlib/gemdos/gemdos.h>
#include <godlib/graphic/graphic.h>
#include <godlib/font8x8/font8x8.h>
#include <godlib/ikbd/ikbd.h>
#include <godlib/memory/memory.h>
#include <godlib/platform/platform.h>
#include <godlib/screen/screen.h>
#include <godlib/vbl/vbl.h>
#include <godlib/video/video.h>
#include "text.h"
extern void MCoder_Update(void),Griff_Update(void),Tiny_CopyPaused(void);
extern void Tiny_RasterSync(const void *physical);
extern U8 gTinyMCBuffer[],gTinyGStorage[],gTinyGBuffer[];
U8 *gTinyPreviousScreen,*gTinyScreen,*gTinyMCText,*gTinyGText,*gTinyGPhaseBase,*gTinyMCDisplay,*gTinyGDisplay;
U16 gTinyMCPhase,gTinyMCPos,gTinyGPhase,gTinyGPos;
volatile U16 gTinyMode=3,gTinyFrameMode,gTinyPaused,gTinyRaster,gTinyReady,gTinyExited;
volatile U32 gTinyFrames,gTinyMCSteps,gTinyGSteps,gTinyFrameMC,gTinyFrameG;
volatile U32 gTinyLastVbl,gTinyMissedVbl;
static void Reset(void)
{
    U16 i;
    sGraphicCanvas *c=Screen_GetpBackGraphic();sGraphicRect r={0,88,320,8};
    gTinyMCText=(U8*)gTinyText;gTinyGText=(U8*)gTinyText;
    gTinyMCPhase=gTinyMCPos=gTinyGPhase=gTinyGPos=0;
    gTinyGPhaseBase=gTinyGBuffer;
    gTinyMCSteps=gTinyGSteps=0;
    Memory_Clear(2560,gTinyMCBuffer);Memory_Clear(16392,gTinyGStorage);
    gTinyScreen=(U8*)Screen_GetpBack();
    /* Original algorithms have different queue latency. After these counts
       both display text pixel 16 at the left edge, with every phase populated. */
    for(i=0;i<169;++i){MCoder_Update();++gTinyMCSteps;}
    for(i=0;i<256;++i){Griff_Update();++gTinyGSteps;}
    GraphicCanvas_DrawBox(c,&r,2);r.mY=120;GraphicCanvas_DrawBox(c,&r,2);
    Font8x8_PrintColourCanvas(gTinyMode==1?"MODE: MCODER ONLY":gTinyMode==2?"MODE: GRIFF ONLY ":"MODE: BOTH      ",c,96,48,6);
    GraphicCanvas_CopyScreen(Screen_GetpLogicGraphic(),Screen_GetpBack());
    GraphicCanvas_CopyScreen(Screen_GetpPhysicGraphic(),Screen_GetpBack());
}
static void Prepare(void)
{
    static U16 pal[16]={0x001,0x777,0x012,0x777,0x034,0x777,0x067,0x777,
                       0x700,0x777,0x770,0x777,0x070,0x777,0x077,0x777};
    sGraphicCanvas *c=Screen_GetpBackGraphic();
    GraphicCanvas_ClearScreen(c);
    Font8x8_PrintColourCanvas("GODLIB / FAST 8X8 SCROLLERS",c,56,16,1);
    Font8x8_PrintColourCanvas("MCODER / 4 PHASES / 2560 BYTES",c,40,72,6);
    Font8x8_PrintColourCanvas("GRIFF / 16 PHASES / 16384 BYTES",c,40,104,6);
    Font8x8_PrintColourCanvas("CPU: GREEN MCODER / ORANGE GRIFF",c,40,136,6);
    Font8x8_PrintColourCanvas("1 MCODER   2 GRIFF   3 BOTH",c,56,152,6);
    Font8x8_PrintColourCanvas("SPACE PAUSE   R CPU   ESC EXIT",c,40,176,1);
    Video_SetPalST(pal);Reset();
}
S16 GodLib_Game_Main(S16 argc,char **argv)
{
    U16 quit=0;U32 last=0;
    (void)argc;(void)argv;GemDos_Super(0);Platform_Init();
    Screen_Init(320,200,eGRAPHIC_COLOURMODE_4PLANE,0);
    if(!gScreenClass.mpMemBase){Platform_DeInit();return 1;}
    Prepare();gTinyReady=1;
    while(!quit) {
        U16 changed=0,meter;U32 now;
        Screen_Update();now=Vbl_GetCounter();
        if(last && now-last>1)gTinyMissedVbl+=now-last-1;
        last=now;gTinyLastVbl=now;IKBD_Update();
        while(IKBD_GetKbdBytesWaiting()) {
            U8 k=IKBD_PopKbdByte();
            if(k==eIKBDSCAN_ESC)quit=1;
            if(k==eIKBDSCAN_SPACE)gTinyPaused^=1;
            if(k==eIKBDSCAN_R)gTinyRaster^=1;
            if(k>=eIKBDSCAN_1 && k<=eIKBDSCAN_3){gTinyMode=k-eIKBDSCAN_1+1;changed=1;}
        }
        if(changed){Reset();gTinyPaused=0;last=Vbl_GetCounter();}
        gTinyScreen=(U8*)Screen_GetpLogic();
        meter=gTinyRaster && !changed;
        if(meter)Tiny_RasterSync(Screen_GetpPhysic());
        if(gTinyPaused) {
            /* MCoder overwrites its outgoing cache byte after drawing. Freeze
               the completed image, rather than drawing that modified cache. */
            if(meter)*(volatile U16*)0xffff8240UL=0x333;
            gTinyPreviousScreen=(U8*)Screen_GetpPhysic();Tiny_CopyPaused();
        } else {
            if(gTinyMode&1){
                if(meter)*(volatile U16*)0xffff8240UL=0x070;
                MCoder_Update();++gTinyMCSteps;
            }
            if(gTinyMode&2){
                if(meter)*(volatile U16*)0xffff8240UL=0x750;
                Griff_Update();++gTinyGSteps;
            }
        }
        if(meter)*(volatile U16*)0xffff8240UL=0x001;
        gTinyFrameMode=gTinyMode;gTinyFrameMC=gTinyMCSteps;gTinyFrameG=gTinyGSteps;
        ++gTinyFrames;
    }
    Screen_DeInit();Platform_DeInit();gTinyExited=1;return 0;
}
