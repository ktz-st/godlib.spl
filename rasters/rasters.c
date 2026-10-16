#include <godlib/gemdos/gemdos.h>
#include <godlib/graphic/graphic.h>
#include <godlib/font8x8/font8x8.h>
#include <godlib/ikbd/ikbd.h>
#include <godlib/memory/memory.h>
#include <godlib/platform/platform.h>
#include <godlib/screen/screen.h>
#include <godlib/system/system.h>
#include <godlib/video/video.h>
#include <stdio.h>
#include "rasters.h"
volatile U16 gRasterReady,gRasterExited;
static void Prepare(void)
{
    static const U16 levels[16]={0,0,1,1,2,3,4,5,7,5,4,3,2,1,1,0};
    U16 i,v; sGraphicCanvas *canvas=Screen_GetpBackGraphic();
    sGraphicRect box; sGraphicBox line;
    for(i=0;i<64;++i) {
        v=levels[i&15];
        switch(i>>4) {
        case 0:gRasterLut[i]=(v<<8)|((v>>1)<<4);break;
        case 1:gRasterLut[i]=(v<<4)|v;break;
        case 2:gRasterLut[i]=(v<<8)|v;break;
        default:gRasterLut[i]=((v>>1)<<8)|(v<<4);break;
        }
    }
    GraphicCanvas_ClearScreen(canvas);
    for(i=0;i<32;++i) {
        box.mX=8+(i*73)%304;box.mY=8+(i*47)%176;
        box.mWidth=box.mHeight=(i&1)?2:1;
        GraphicCanvas_DrawBox(canvas,&box,15);
    }
    line.mX0=96;line.mY0=96;line.mX1=160;line.mY1=40;
    GraphicCanvas_DrawLine(canvas,&line,15);
    line.mX0=160;line.mY0=40;line.mX1=224;line.mY1=96;
    GraphicCanvas_DrawLine(canvas,&line,15);
    line.mX0=224;line.mY0=96;line.mX1=160;line.mY1=152;
    GraphicCanvas_DrawLine(canvas,&line,15);
    line.mX0=160;line.mY0=152;line.mX1=96;line.mY1=96;
    GraphicCanvas_DrawLine(canvas,&line,15);
    Font8x8_PrintColourCanvas("GODLIB RASTERS",canvas,104,16,15);
    Font8x8_PrintColourCanvas("TIMER B",canvas,136,80,15);
    Font8x8_PrintColourCanvas("49 CHANGES",canvas,120,96,15);
    Font8x8_PrintColourCanvas("ONE COLOUR",canvas,120,112,15);
    Font8x8_PrintColourCanvas("SPACE PAUSE  R ON/OFF  ESC EXIT",canvas,40,184,15);
    Memory_Copy(32000UL,Screen_GetpBack(),Screen_GetpLogic());
    Memory_Copy(32000UL,Screen_GetpBack(),Screen_GetpPhysic());
}
S16 GodLib_Game_Main(S16 argc,char **argv)
{
    U8 quit=0;U16 vdo;
    (void)argc;(void)argv;GemDos_Super(0);Platform_Init();vdo=System_GetVDO();
    if(vdo!=VDO_ST && vdo!=VDO_STE) {
        printf("Rasters require ST/STE PAL low resolution.\n");
        Platform_DeInit();return 1;
    }
    Screen_Init(320,200,eGRAPHIC_COLOURMODE_4PLANE,0);
    if(!gScreenClass.mpMemBase) {Platform_DeInit();return 1;}
    Prepare();Raster_Init();gRasterReady=1;
    while(!quit) {
        IKBD_Update();
        while(IKBD_GetKbdBytesWaiting()) {
            U8 key=IKBD_PopKbdByte();
            if(key==eIKBDSCAN_ESC)quit=1;
            if(key==eIKBDSCAN_SPACE)gRasterAnimate^=1;
            if(key==eIKBDSCAN_R)gRasterEnabled^=1;
            if(key==eIKBDSCAN_1)gRasterSpeed=1;
            if(key==eIKBDSCAN_2)gRasterSpeed=2;
        }
        Screen_Update();
    }
    Raster_DeInit();gRasterPalette[0]=0x012;Video_SetPalST(gRasterPalette);
    Screen_Update();Screen_DeInit();Platform_DeInit();
    gRasterExited=1;return 0;
}
