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
extern U16 gHSplitPicture[];
static U8 sPanelMemory[2560+255];
sGraphicCanvas gHSplitPanelCanvas;
volatile U16 gHSplitReady,gHSplitExited;
U16 gHSplitX,gHSplitAuto=1,gHSplitSpeed=1;
static void DrawPanel(void)
{
    sGraphicRect line={0,0,320,1};
    sGraphicCanvas *canvas=&gHSplitPanelCanvas;
    GraphicCanvas_Init(&gHSplitPanelCanvas,eGRAPHIC_COLOURMODE_4PLANE,320,16);
    gHSplitPanelCanvas.mpVRAM=(void*)(((U32)sPanelMemory+255UL)&~255UL);
    GraphicCanvas_ClearScreen(canvas);
    GraphicCanvas_DrawBox(canvas,&line,15);
    line.mY=15;GraphicCanvas_DrawBox(canvas,&line,15);
    Font8x8_PrintColourCanvas("FIXED HUD / SPACE PAUSE / ESC EXIT",&gHSplitPanelCanvas,8,4,15);
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
    Screen_Init(640,200,eGRAPHIC_COLOURMODE_4PLANE,eSCREEN_SCROLL_H);
    if(!gScreenClass.mpMemBase) {Platform_DeInit();return 1;}
    /* Video stays 320x200. Only its lower 184 rows use the wide terrain. */
    Video_SetPalST(gHSplitPicture);
    Memory_Copy(64000UL,gHSplitPicture+16,Screen_GetpBack());
    Memory_Copy(64000UL,Screen_GetpBack(),Screen_GetpLogic());
    Memory_Copy(64000UL,Screen_GetpBack(),Screen_GetpPhysic());
    DrawPanel();HSplit_Init(gHSplitPanelCanvas.mpVRAM);gHSplitReady=1;
    while(!quit) {
        IKBD_Update();
        while(IKBD_GetKbdBytesWaiting()) {
            U8 key=IKBD_PopKbdByte();
            if(key==eIKBDSCAN_ESC)quit=1;
            if(key==eIKBDSCAN_SPACE)gHSplitAuto^=1;
            if(key==eIKBDSCAN_1)gHSplitSpeed=1;
            if(key==eIKBDSCAN_2)gHSplitSpeed=4;
        }
        if(gHSplitAuto) {
            if(gHSplitX>=320)step=-1;
            if(!gHSplitX)step=1;
            {S16 next=(S16)gHSplitX+step*gHSplitSpeed;
             gHSplitX=next<0?0:next>320?320:(U16)next;}
        } else {
            if(IKBD_GetKeyStatus(eIKBDSCAN_LEFTARROW) && gHSplitX)--gHSplitX;
            if(IKBD_GetKeyStatus(eIKBDSCAN_RIGHTARROW) && gHSplitX<320)++gHSplitX;
        }
        Screen_SetScrollX(gHSplitX);Screen_Update();
    }
    HSplit_DeInit();
    /* Present a normal page before releasing screen memory. */
    Screen_SetScrollX(0);Screen_Update();
    GraphicCanvas_DeInit(&gHSplitPanelCanvas);
    Screen_DeInit();Platform_DeInit();gHSplitExited=1;return 0;
}
