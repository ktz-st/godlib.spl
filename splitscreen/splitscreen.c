#include <godlib/gemdos/gemdos.h>
#include <godlib/ikbd/ikbd.h>
#include <godlib/font8x8/font8x8.h>
#include <godlib/graphic/graphic.h>
#include <godlib/memory/memory.h>
#include <godlib/platform/platform.h>
#include <godlib/screen/screen.h>
#include <godlib/system/system.h>
#include <godlib/video/video.h>
#include <godlib/vbl/vbl.h>
#include <stdio.h>
#include "split.h"
extern U16 gSplitPicture[];
static U8 sPanelMemory[6400+255];
sGraphicCanvas gSplitPanelCanvas;
volatile U16 gSplitReady,gSplitExited;
U16 gSplitY,gSplitAuto=1,gSplitSpeed=1;
static void DrawPanel(void)
{
    sGraphicRect line={0,0,320,1};
    sGraphicCanvas *canvas=&gSplitPanelCanvas;
    GraphicCanvas_Init(&gSplitPanelCanvas,eGRAPHIC_COLOURMODE_4PLANE,320,40);
    gSplitPanelCanvas.mpVRAM=(void*)(((U32)sPanelMemory+255UL)&~255UL);
    GraphicCanvas_ClearScreen(canvas);
    GraphicCanvas_DrawBox(canvas,&line,15);
    line.mY=39;GraphicCanvas_DrawBox(canvas,&line,15);
    Font8x8_PrintColourCanvas("TIMER B SPLIT / 160 + 40",&gSplitPanelCanvas,8,8,15);
    Font8x8_PrintColourCanvas("SPACE PAUSE UP/DOWN ESC EXIT",&gSplitPanelCanvas,8,24,15);
}
S16 GodLib_Game_Main(S16 argc,char **argv)
{
    U8 quit=0;S16 step=1;
    (void)argc;(void)argv;
    GemDos_Super(0);Platform_Init();
    if(System_GetVDO()!=VDO_STE) {
        printf("Split screen: STE video hardware required.\n");
        Platform_DeInit();return 1;
    }
    Screen_Init(320,400,eGRAPHIC_COLOURMODE_4PLANE,eSCREEN_SCROLL_V);
    if(!gScreenClass.mpMemBase) {Platform_DeInit();return 1;}
    /* Video remains 320x200; only 160 rows come from the scrolled terrain. */
    gScreenClass.mViewportHeight=160;
    Video_SetPalST(gSplitPicture);
    Memory_Copy(64000UL,gSplitPicture+16,Screen_GetpBack());
    Memory_Copy(64000UL,Screen_GetpBack(),Screen_GetpLogic());
    Memory_Copy(64000UL,Screen_GetpBack(),Screen_GetpPhysic());
    DrawPanel();Split_Init(gSplitPanelCanvas.mpVRAM);gSplitReady=1;
    while(!quit) {
        IKBD_Update();
        while(IKBD_GetKbdBytesWaiting()) {
            U8 key=IKBD_PopKbdByte();
            if(key==eIKBDSCAN_ESC)quit=1;
            if(key==eIKBDSCAN_SPACE)gSplitAuto^=1;
            if(key==eIKBDSCAN_1)gSplitSpeed=1;
            if(key==eIKBDSCAN_2)gSplitSpeed=4;
        }
        if(gSplitAuto) {
            if(gSplitY>=240)step=-1;
            if(!gSplitY)step=1;
            {S16 next=(S16)gSplitY+step*gSplitSpeed;
             gSplitY=next<0?0:next>240?240:(U16)next;}
        } else {
            if(IKBD_GetKeyStatus(eIKBDSCAN_UPARROW) && gSplitY)--gSplitY;
            if(IKBD_GetKeyStatus(eIKBDSCAN_DOWNARROW) && gSplitY<240)++gSplitY;
        }
        Screen_SetScrollY(gSplitY);Screen_Update();
    }
    Split_DeInit();
    /* Present a normal page before releasing screen memory. */
    Screen_SetScrollY(0);Screen_Update();
    GraphicCanvas_DeInit(&gSplitPanelCanvas);
    Screen_DeInit();Platform_DeInit();gSplitExited=1;return 0;
}
