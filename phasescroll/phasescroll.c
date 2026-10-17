#include <godlib/gemdos/gemdos.h>
#include <godlib/ikbd/ikbd.h>
#include <godlib/font8x8/font8x8.h>
#include <godlib/graphic/graphic.h>
#include <godlib/memory/memory.h>
#include <godlib/platform/platform.h>
#include <godlib/screen/screen.h>
#include <godlib/system/system.h>
#include <godlib/vbl/vbl.h>
#include <stdio.h>
#include "phase.h"
U16 gHSplitHudPalette[16]={0x012,0x024,0x036,0x047,0x057,0x067,0x077,0x177,
                         0x277,0x377,0x477,0x577,0x677,0x777,0x750,0x770};
volatile U32 gPhasePending,gPhaseFrames,gPhaseMissedVbl,gPhaseLastVbl;
volatile U16 gPhaseFine,gPhasePendingX,gPhaseShownX,gPhaseReady,gPhaseExited;
volatile U16 gPhaseMagnitude=1,gPhaseRaster;
volatile S16 gPhaseDirection=1;
static void Publish(void)
{
    U16 iml=System_GetIML();System_SetIML(7);
    gPhasePending=(U32)Phase_State.screen;
    gPhaseFine=Phase_State.x&15;gPhasePendingX=Phase_State.x;
    System_SetIML(iml);
}
static void Panel(void)
{
    sGraphicCanvas c,*canvas=&c;sGraphicRect r={0,39,320,1};
    GraphicCanvas_Init(&c,eGRAPHIC_COLOURMODE_4PLANE,320,40);
    c.mpVRAM=Screen_GetpBack();GraphicCanvas_ClearScreen(canvas);
    Font8x8_PrintColourCanvas("GODLIB / STE PHASE SCROLLING",&c,48,2,15);
    Font8x8_PrintColourCanvas("1/2/4/8 SPEED  0 PAUSE  SPACE REVERSE",&c,16,14,13);
    Font8x8_PrintColourCanvas("LEFT/RIGHT DIRECTION  R CPU  ESC EXIT",&c,16,26,13);
    GraphicCanvas_DrawBox(canvas,&r,14);GraphicCanvas_DeInit(&c);
}
S16 GodLib_Game_Main(S16 argc,char **argv)
{
    U8 quit=0;void *allocation;U32 last=0;
    (void)argc;(void)argv;GemDos_Super(0);Platform_Init();
    if(System_GetVDO()!=VDO_STE || System_GetBLT()!=BLT_BLITTER) {
        printf("Phase scrolling requires an STE and BLiTTER.\n");Platform_DeInit();return 1;
    }
    Screen_Init(320,200,eGRAPHIC_COLOURMODE_4PLANE,0);
    if(!gScreenClass.mpMemBase){Platform_DeInit();return 1;}
    /* Both 32K regions fit in one 64K bank: the original low-word BLiTTER
       address updates remain valid, without fixed $60000/$70000 addresses. */
    allocation=Memory_ScreenCalloc(131071UL);
    if(!allocation){Screen_DeInit();Platform_DeInit();return 1;}
    Phase_Tiles=(U8*)(((U32)allocation+65535UL)&~65535UL);
    Phase_State.buffer=Phase_Tiles+32768;
    Phase_State.screen=Phase_State.buffer+8+12*8;
    Memory_Copy(32768UL,Phase_TileAsset,Phase_Tiles);
    Panel();Phase_Init();Publish();
    HSplit_Init(Screen_GetpBack());gPhaseReady=1;
    while(!quit) {
        U32 now;
        Screen_Update();now=Vbl_GetCounter();
        if(last && now-last>1)gPhaseMissedVbl+=now-last-1;
        last=now;gPhaseLastVbl=now;IKBD_Update();
        while(IKBD_GetKbdBytesWaiting()) {
            U8 k=IKBD_PopKbdByte();
            if(k==eIKBDSCAN_ESC)quit=1;
            if(k==eIKBDSCAN_SPACE)gPhaseDirection=-gPhaseDirection;
            if(k==eIKBDSCAN_LEFTARROW)gPhaseDirection=-1;
            if(k==eIKBDSCAN_RIGHTARROW)gPhaseDirection=1;
            if(k==eIKBDSCAN_0)gPhaseMagnitude=0;
            if(k==eIKBDSCAN_1)gPhaseMagnitude=1;
            if(k==eIKBDSCAN_2)gPhaseMagnitude=2;
            if(k==eIKBDSCAN_4)gPhaseMagnitude=4;
            if(k==eIKBDSCAN_8)gPhaseMagnitude=8;
            if(k==eIKBDSCAN_R)gPhaseRaster^=1;
        }
        Phase_State.speed=gPhaseDirection*(S16)gPhaseMagnitude;
        if(gPhaseRaster)*(volatile U16*)0xffff8240UL=0x070;
        Phase_Step();Publish();
        if(gPhaseRaster)*(volatile U16*)0xffff8240UL=0x012;
        if(Phase_State.x==0)gPhaseDirection=1;
        if(Phase_State.x==1984)gPhaseDirection=-1;
        ++gPhaseFrames;
    }
    HSplit_DeInit();Screen_Update();
    Memory_ScreenRelease(allocation);Screen_DeInit();Platform_DeInit();gPhaseExited=1;return 0;
}
