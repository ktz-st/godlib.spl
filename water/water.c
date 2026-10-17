#include <godlib/gemdos/gemdos.h>
#include <godlib/ikbd/ikbd.h>
#include <godlib/memory/memory.h>
#include <godlib/platform/platform.h>
#include <godlib/screen/screen.h>
#include <godlib/vbl/vbl.h>
#include <godlib/video/video.h>
#include "assets/config.h"
extern void Water_Draw(void);
extern U16 Water_Picture[],Water_Rows[];
extern U8 Water_Surface[];
U8 *gWaterScreen,*gWaterSurfaceCursor,*gWaterOldSurface;
U16 *gWaterCursor,*gWaterOldCursor;
static U16 *sRows[2];
static U8 *sSurface[2];
volatile U16 gWaterReady,gWaterExited,gWaterPaused,gWaterEnabled=1;
volatile U16 gWaterTick,gWaterSurfaceTick,gWaterSpeed=1;
volatile U16 gWaterFrameTick,gWaterFrameSurface,gWaterFrameEnabled;
volatile U32 gWaterFrames,gWaterLastVbl,gWaterMissedVbl;
static void Advance(U16 ticks)
{
    U16 next=gWaterTick+ticks,surface=gWaterSurfaceTick+ticks;
    while(next>=WATER_STATES)next-=WATER_STATES;
    while(surface>=20)surface-=20;
    gWaterTick=next;gWaterSurfaceTick=surface;
}
static void __attribute__((noinline)) Commands(void)
{
    static const U16 frames[4]={0,1,2,1};
    U16 page=Screen_GetLogicIndex();
    gWaterFrameTick=gWaterTick;gWaterFrameEnabled=gWaterEnabled;
    gWaterCursor=Water_Rows+(U32)(gWaterEnabled?gWaterTick:WATER_STATES)*WATER_HEIGHT;
    gWaterFrameSurface=gWaterEnabled?frames[gWaterSurfaceTick/5]:3;
    gWaterSurfaceCursor=gWaterEnabled?Water_Surface+gWaterFrameSurface*160:
        (U8*)Water_Picture+34+(WATER_TOP-1)*160;
    gWaterOldCursor=sRows[page];gWaterOldSurface=sSurface[page];
    sRows[page]=gWaterCursor;sSurface[page]=gWaterSurfaceCursor;
    gWaterScreen=(U8*)Screen_GetpLogic();
}
S16 GodLib_Game_Main(S16 argc,char **argv)
{
    U16 quit=0;
    (void)argc;(void)argv;GemDos_Super(0);Platform_Init();
    Screen_Init(320,200,eGRAPHIC_COLOURMODE_4PLANE,0);
    if(!gScreenClass.mpMemBase){Platform_DeInit();return 1;}
    Memory_Copy(32000UL,(U8*)Water_Picture+34,Screen_GetpLogic());
    Memory_Copy(32000UL,(U8*)Water_Picture+34,Screen_GetpPhysic());
    Video_SetPalST(Water_Picture+1);
    sRows[0]=sRows[1]=Water_Rows+(U32)WATER_STATES*WATER_HEIGHT;
    sSurface[0]=sSurface[1]=(U8*)Water_Picture+34+(WATER_TOP-1)*160;
    gWaterLastVbl=Vbl_GetCounter();gWaterReady=1;
    while(!quit) {
        U32 now,elapsed;U16 step=0;
        Screen_Update();now=Vbl_GetCounter();elapsed=now-gWaterLastVbl;
        if(gWaterFrames && elapsed>1)gWaterMissedVbl+=elapsed-1;
        gWaterLastVbl=now;IKBD_Update();
        while(IKBD_GetKbdBytesWaiting()) {
            U8 k=IKBD_PopKbdByte();
            if(k==eIKBDSCAN_ESC)quit=1;
            if(k==eIKBDSCAN_SPACE)gWaterPaused^=1;
            if(k==eIKBDSCAN_N){gWaterPaused=1;step=1;}
            if(k==eIKBDSCAN_W)gWaterEnabled^=1;
            if(k>=eIKBDSCAN_1 && k<=eIKBDSCAN_3)gWaterSpeed=1<<(k-eIKBDSCAN_1);
        }
        if(step)Advance(1);
        else if(!gWaterPaused)Advance((U16)(elapsed*gWaterSpeed));
        Commands();Water_Draw();++gWaterFrames;
    }
    Screen_DeInit();Platform_DeInit();gWaterExited=1;return 0;
}
