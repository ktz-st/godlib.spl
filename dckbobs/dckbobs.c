#include "dckbobs.h"
#include <godlib/gemdos/gemdos.h>
#include <godlib/font8x8/font8x8.h>
#include <godlib/ikbd/ikbd.h>
#include <godlib/platform/platform.h>
#include <godlib/screen/screen.h>
#include <godlib/system/system.h>
#include <godlib/vbl/vbl.h>
#include <godlib/video/video.h>
#include <stdio.h>
#include <string.h>

sGraphicPos gBobsPositions[8],gBobsPrevious[8];
U16 gBobsIndices[8];
sGraphicChunkList gBobsChunks[2],*gBobsList;
sGraphicCanvas *gBobsCanvas,*gBobsBackCanvas;
void (*gBobsDrawFn)(sGraphicCanvas *,sGraphicPos *,void *);
volatile U16 gBobsCount=4,gBobsPath,gBobsTrails,gBobsPaused,gBobsBlitter,gBobsReady,gBobsExited,gBobsRaster;
volatile U32 gBobsFrames,gBobsMissedVbl;
static sGraphicCanvas sCanvas[2]; /* Borrow Screen's row offsets; Screen owns them. */
#ifdef BOBS_BENCH
volatile U16 gBobsHold,gBobsRequest,gBobsCompleted,gBobsReset,gBobsTestPage;
volatile U32 gBobsCalls;
#endif
static void Target(U16 page)
{
    gBobsCanvas=&sCanvas[page];gBobsList=&gBobsChunks[page];
    gBobsDrawFn=gBobsCanvas->mpFuncs->DrawSprite;
}
static void Scene(void)
{
    static const char *names[]={"NOEUD","CERCLE","2CERCLES","DOUBLE45","CER-45","CER_45B","GROS_CER","REBOND"};
    sGraphicCanvas *c=Screen_GetpBackGraphic();sGraphicRect r;U16 i;char text[41];
    GraphicCanvas_ClearScreen(c);
    r.mY=32;r.mHeight=136;r.mWidth=1;
    for(i=0;i<320;i+=16){r.mX=i;GraphicCanvas_DrawBox(c,&r,6);}
    r.mX=0;r.mWidth=320;r.mHeight=1;
    for(i=32;i<168;i+=16){r.mY=i;GraphicCanvas_DrawBox(c,&r,6);}
    Font8x8_PrintColourCanvas("DCK BOBS / GODLIB SPRITES",c,64,0,15);
    sprintf(text,"%s  %u BOBS  %s",names[gBobsPath],gBobsCount,gBobsBlitter?"BLITTER":"CPU");
    Font8x8_PrintColourCanvas(text,c,(40-(U16)strlen(text))/2*8,10,15);
    Font8x8_PrintColourCanvas(gBobsTrails?"TRAILS / EVERY FRAME ON BOTH PAGES":"RESTORE / GODLIB ASM CHUNK LIST",c,gBobsTrails?24:40,20,15);
    Font8x8_PrintColourCanvas("1/2/3: 1/4/8 BOBS  P: PATH  B: BLT",c,24,176,15);
    Font8x8_PrintColourCanvas("T: RESTORE/TRAILS  C: CLEAR",c,56,184,15);
    Font8x8_PrintColourCanvas("SPACE: PAUSE  R: CPU  ESC: EXIT",c,40,192,15);
}
static void Reset(void)
{
    U16 p;
    Graphic_SetBlitterEnable(gBobsBlitter);gBobsBlitter=Graphic_GetBlitterEnable();
    Bobs_Init();Scene();
    /* Mode/path changes start a new history. Seed BOTH pages with frame zero,
       so trail catch-up never leaves its first stamp missing on one page. */
    for(p=0;p<2;++p){
        gBobsChunks[p].mChunkCount=32;Graphic_ChunkList_Clear(&gBobsChunks[p]);
        sCanvas[p].mpFuncs->CopyScreen(&sCanvas[p],Screen_GetpBack());
        Target(p);Bobs_Seed();Bobs_Store();
    }
}
S16 GodLib_Game_Main(S16 argc,char **argv)
{
    U16 quit=0,p;U32 last=0;
    (void)argc;(void)argv;GemDos_Super(0);Platform_Init();
    Screen_Init(320,200,eGRAPHIC_COLOURMODE_4PLANE,0);
    if(!gScreenClass.mpMemBase){Platform_DeInit();return 1;}
    for(p=0;p<2;++p){sCanvas[p]=*Screen_GetpLogicGraphic();sCanvas[p].mpVRAM=gScreenClass.mpBuffers[p];}
    gBobsBackCanvas=Screen_GetpBackGraphic();gBobsBlitter=System_GetBLT()==BLT_BLITTER;
    Reset();Video_SetPalST(Bobs_Palette);gBobsReady=1;
    while(!quit){
#ifdef BOBS_BENCH
        if(gBobsHold){
            if(gBobsRequest){U16 request=gBobsRequest,n,iterations=request==2?Bobs_Lengths[gBobsPath]:1;gBobsRequest=0;
                if(gBobsReset){Reset();gBobsTestPage=0;gBobsReset=0;}
                gBobsCalls=0;
                for(n=0;n<iterations;++n){Target(gBobsTestPage);Bobs_Frame();gBobsTestPage^=1;++gBobsCalls;}
                gBobsCompleted=request;
            }
            continue;
        }
#endif
        Screen_Update();
        {U32 now=Vbl_GetCounter();if(last && now-last>1)gBobsMissedVbl+=now-last-1;last=now;}
        IKBD_Update();
        while(IKBD_GetKbdBytesWaiting()){
            U8 k=IKBD_PopKbdByte();U16 reset=0;
            if(k==eIKBDSCAN_ESC)quit=1;
            if(k==eIKBDSCAN_SPACE)gBobsPaused^=1;
            if(k==eIKBDSCAN_R)gBobsRaster^=1;
            if(k==eIKBDSCAN_T){gBobsTrails^=1;reset=1;}
            if(k==eIKBDSCAN_P){gBobsPath=(gBobsPath+1)&7;reset=1;}
            if(k==eIKBDSCAN_B){gBobsBlitter^=1;reset=1;}
            if(k>=eIKBDSCAN_1 && k<=eIKBDSCAN_3){gBobsCount=k==eIKBDSCAN_1?1:k==eIKBDSCAN_2?4:8;reset=1;}
            if(k==eIKBDSCAN_C)reset=1;
            if(reset)Reset();
        }
        Target(Screen_GetLogicIndex());
        if(gBobsRaster)*(volatile U16*)0xffff8240UL=0x070;
        Bobs_Frame();
        if(gBobsRaster)*(volatile U16*)0xffff8240UL=0;
        ++gBobsFrames;
    }
    Screen_DeInit();Platform_DeInit();gBobsExited=1;return 0;
}
