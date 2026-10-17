#include <godlib/gemdos/gemdos.h>
#include <godlib/ikbd/ikbd.h>
#include <godlib/memory/memory.h>
#include <godlib/platform/platform.h>
#include <godlib/screen/screen.h>
#include <godlib/system/system.h>
#include <godlib/video/video.h>
#include <stdio.h>
#include "palsplit.h"
extern U16 gPalSplitPicture[];
volatile U16 gPalSplitReady,gPalSplitExited;
static void BuildGreyPalette(void)
{
    U16 i;
    for(i=0;i<16;++i) {
        U16 c=gPalSplitPicture[i+1];
        U16 r=(c>>8)&15,g=(c>>4)&15,b=c&15,y;
        if(System_GetVDO()==VDO_STE) {
            /* STE nibbles store the least significant bit in bit 3. */
            r=((r&7)<<1)|(r>>3);g=((g&7)<<1)|(g>>3);b=((b&7)<<1)|(b>>3);
            y=(77*r+150*g+29*b+128)>>8;
            y=(y>>1)|((y&1)<<3);
        } else {
            r&=7;g&=7;b&=7;
            y=(77*r+150*g+29*b+128)>>8;
        }
        gPalSplitGrey[i]=y*0x111;
    }
}
S16 GodLib_Game_Main(S16 argc,char **argv)
{
    U8 quit=0;U16 vdo;
    (void)argc;(void)argv;
    GemDos_Super(0);Platform_Init();vdo=System_GetVDO();
    if(vdo!=VDO_ST && vdo!=VDO_STE) {
        printf("Palette split requires ST/STE PAL low resolution.\n");
        Platform_DeInit();return 1;
    }
    Screen_Init(320,200,eGRAPHIC_COLOURMODE_4PLANE,0);
    if(!gScreenClass.mpMemBase) {Platform_DeInit();return 1;}
    BuildGreyPalette();Video_SetPalST(gPalSplitPicture+1);
    Memory_Copy(32000UL,gPalSplitPicture+17,Screen_GetpBack());
    Memory_Copy(32000UL,Screen_GetpBack(),Screen_GetpLogic());
    Memory_Copy(32000UL,Screen_GetpBack(),Screen_GetpPhysic());
    PalSplit_Init();gPalSplitReady=1;
    while(!quit) {
        IKBD_Update();
        while(IKBD_GetKbdBytesWaiting()) {
            U8 key=IKBD_PopKbdByte();
            if(key==eIKBDSCAN_ESC)quit=1;
            if(key==eIKBDSCAN_SPACE)gPalSplitEnabled^=1;
        }
        Screen_Update();
    }
    PalSplit_DeInit();
    Video_SetPalST(gPalSplitPicture+1);Screen_Update();
    Screen_DeInit();Platform_DeInit();gPalSplitExited=1;return 0;
}
