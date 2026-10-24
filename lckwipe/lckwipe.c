#include "lckwipe.h"
#include <godlib/gemdos/gemdos.h>
#include <godlib/font8x8/font8x8.h>
#include <godlib/graphic/graphic.h>
#include <godlib/ikbd/ikbd.h>
#include <godlib/platform/platform.h>
#include <godlib/screen/screen.h>
#include <godlib/vbl/vbl.h>
#include <godlib/video/video.h>
#include <stdio.h>

U8 *gLwDest;
const U8 *gLwSource;
S16 *gLwRows;
U16 *gLwOld,gLwPrevious[2];
S16 gLwRowHistory[2][160];
U16 gLwColMasks[20];
const U16 *gLwStages,*gLwNextPalette;
volatile U16 gLwEffect,gLwTarget,gLwClosing,gLwPhase,gLwImage,gLwPaused,gLwRaster,gLwReady,gLwExited;
volatile U16 gLwClock;
volatile U32 gLwFrames,gLwMissedVbl,gLwSwaps,gLwTransitions;
static U16 sHeaderSerial,sPageHeader[2];
static const U16 *sQueuedPalette;
#ifdef LW_BENCH
volatile U16 gLwHold,gLwRequest,gLwCompleted,gLwTestReset,gLwTestPage,gLwHoldOnBlack,gLwAtBlack;
volatile U32 gLwCalls;
#endif
static void Target(U16 page)
{
    gLwDest=(U8*)gScreenClass.mpBuffers[page]+24*160;
    gLwRows=gLwRowHistory[page];gLwOld=&gLwPrevious[page];
}
static void Source(void)
{
    gLwSource=gLwImage?Lw_Picture1:Lw_Picture0;gLwStages=gLwImage?Lw_Stages1:Lw_Stages0;
    gLwNextPalette=gLwImage?Lw_Palette1:Lw_Palette0;sQueuedPalette=0;
}
static void PublishPalette(void)
{
    if(sQueuedPalette!=gLwNextPalette){Video_SetNextPalST(gLwNextPalette);sQueuedPalette=gLwNextPalette;}
}
static void Advance(void)
{
    if(gLwEffect==LW_COLOURS && ++gLwClock<5)return;
    gLwClock=0;gLwTarget+=Lw_Speeds[gLwEffect];
    if(gLwTarget>Lw_Limits[gLwEffect])gLwTarget=Lw_Limits[gLwEffect];
}
static void Header(void)
{
    static const char *names[]={"SPIRAL 8X8","FOLD","ALTERNATING LINES","SNAKE 16X10","INSTANT","COLOUR STEPS","CENTRE ROWS","ROW SMEAR","INTERLACED ROWS","VERTICAL CURTAIN","INTERLACED COLS"};
    static const char *states[]={"READY","CLOSING","OPENING"};
    sGraphicCanvas *c=Screen_GetpBackGraphic();sGraphicRect r={0,16,320,8};char text[41];
    GraphicCanvas_DrawBox(c,&r,0);
    sprintf(text,"%02u/11 %s / %s / %u",gLwEffect+1,names[gLwEffect],states[gLwPhase],gLwImage+1);
    Font8x8_PrintColourCanvas(text,c,0,16,15);++sHeaderSerial;
}
static void FlushHeader(U16 page)
{
    if(sPageHeader[page]!=sHeaderSerial){
        sGraphicPos p={0,16};sGraphicRect r={0,16,320,8};
        Screen_Logic_Blit(&p,&r,Screen_GetpBackGraphic());sPageHeader[page]=sHeaderSerial;
    }
}
static void ClearPages(U16 show)
{
    U16 p;sGraphicCanvas canvas=*Screen_GetpLogicGraphic();
    for(p=0;p<2;++p){
        canvas.mpVRAM=gScreenClass.mpBuffers[p];canvas.mpFuncs->CopyScreen(&canvas,Screen_GetpBack());
        Target(p);if(show)Lw_Show();sPageHeader[p]=sHeaderSerial;
    }
}
static void NextPhase(void)
{
    if(gLwClosing){
#ifdef LW_BENCH
        if(gLwHoldOnBlack){gLwAtBlack=1;return;}
        gLwAtBlack=0;
#endif
        /* Both display pages have reached black before changing image/palette. */
        gLwImage^=1;Source();gLwClosing=0;gLwPhase=2;gLwTarget=0;gLwClock=0;Lw_Begin();
        PublishPalette();++gLwSwaps;
    }else{gLwPhase=0;++gLwTransitions;}
    Header();
}
S16 GodLib_Game_Main(S16 argc,char **argv)
{
    U16 quit=0;U32 last=0;sGraphicCanvas *back;
    (void)argc;(void)argv;GemDos_Super(0);Platform_Init();
    Screen_Init(320,200,eGRAPHIC_COLOURMODE_4PLANE,0);
    if(!gScreenClass.mpMemBase){Platform_DeInit();return 1;}
    Graphic_SetBlitterEnable(0);Source();back=Screen_GetpBackGraphic();GraphicCanvas_ClearScreen(back);
    Font8x8_PrintColourCanvas("LCK / BITMAP TRANSITIONS",back,64,0,15);
    Font8x8_PrintColourCanvas("LEFT/RIGHT EFFECT   N NEXT IMAGE",back,0,8,15);
    Font8x8_PrintColourCanvas("1-4 SHORTCUTS   SPACE PAUSE",back,0,184,15);
    Font8x8_PrintColourCanvas("R CPU STRIPE               ESC EXIT",back,0,192,15);
    Header();ClearPages(1);Video_SetPalST(Lw_Palette0);gLwReady=1;
    while(!quit){
#ifdef LW_BENCH
        if(gLwHold){
            if(gLwRequest){
                U16 request=gLwRequest;gLwRequest=0;gLwCalls=0;
                if(gLwTestReset){Source();Video_SetPalST(gLwImage?Lw_Palette1:Lw_Palette0);gLwPhase=gLwClosing?1:2;gLwTarget=0;gLwClock=0;Header();ClearPages(gLwClosing);Lw_Begin();gLwTestPage=0;gLwTestReset=0;}
                if(request==2){
                    while(gLwTarget<Lw_Limits[gLwEffect]){
                        Advance();
                        Target(gLwTestPage);Lw_Render();gLwTestPage^=1;++gLwCalls;
                    }
                }
                Target(gLwTestPage);Lw_Render();gLwTestPage^=1;++gLwCalls;
                PublishPalette();
                gLwCompleted=request;
            }
            continue;
        }
#endif
        Screen_Update();
        {U32 now=Vbl_GetCounter();if(last && now-last>1)gLwMissedVbl+=now-last-1;last=now;}
        IKBD_Update();
        while(IKBD_GetKbdBytesWaiting()){
            U8 k=IKBD_PopKbdByte();
            if(k==eIKBDSCAN_ESC)quit=1;
            if(k==eIKBDSCAN_R)gLwRaster^=1;
            if(k==eIKBDSCAN_SPACE)gLwPaused^=1;
            if(!gLwPhase){
                if(k>=eIKBDSCAN_1 && k<=eIKBDSCAN_4){gLwEffect=k-eIKBDSCAN_1;Header();}
                if(k==eIKBDSCAN_LEFTARROW){gLwEffect=gLwEffect?gLwEffect-1:LW_EFFECT_COUNT-1;Header();}
                if(k==eIKBDSCAN_RIGHTARROW){gLwEffect=(gLwEffect+1)%LW_EFFECT_COUNT;Header();}
                if(k==eIKBDSCAN_N){gLwClosing=1;gLwPhase=1;gLwTarget=0;gLwClock=0;Lw_Begin();Header();}
            }
        }
        {U16 page=Screen_GetLogicIndex();Target(page);FlushHeader(page);}
        if(gLwPhase){
            if(!gLwPaused)Advance();
            if(gLwRaster)*(volatile U16*)0xffff8240UL=0x070;
            Lw_Render();
            if(gLwRaster)*(volatile U16*)0xffff8240UL=0;
            PublishPalette();
            if(!gLwPaused && gLwPrevious[0]==Lw_Limits[gLwEffect] && gLwPrevious[1]==Lw_Limits[gLwEffect])NextPhase();
        }
        ++gLwFrames;
    }
    Screen_DeInit();Platform_DeInit();gLwExited=1;return 0;
}
