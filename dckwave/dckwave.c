#include "dckwave.h"
#include <godlib/gemdos/gemdos.h>
#include <godlib/font8x8/font8x8.h>
#include <godlib/graphic/graphic.h>
#include <godlib/ikbd/ikbd.h>
#include <godlib/platform/platform.h>
#include <godlib/screen/screen.h>
#include <godlib/vbl/vbl.h>
#include <godlib/video/video.h>

U8 *gDwDest;
const U8 *gDwCursor,*gDwPrevious[2],**gDwOldCursor;
U16 *gDwOldMask,gDwPreviousMask[2];
volatile U16 gDwMode,gDwMask=15,gDwPhase,gDwPaused,gDwRaster,gDwReady,gDwExited;
volatile U32 gDwFrames,gDwMissedVbl;
static U16 sHeaderSerial,sPageHeader[2];
#ifdef DW_BENCH
volatile U16 gDwHold,gDwRequest,gDwCompleted,gDwReset,gDwTestPage;
volatile U32 gDwCalls;
#endif
static void Target(U16 page)
{
    gDwDest=(U8*)gScreenClass.mpBuffers[page]+24*160;
    gDwOldCursor=&gDwPrevious[page];gDwOldMask=&gDwPreviousMask[page];
}
static void Header(void)
{
    static const char *names[]={"ALL PLANES 0+1+2+3","ONE PLANE 1","TWO PLANES 0+2"};
    sGraphicCanvas *c=Screen_GetpBackGraphic();sGraphicRect r={0,16,320,8};
    GraphicCanvas_DrawBox(c,&r,0);Font8x8_PrintColourCanvas(names[gDwMode],c,0,16,14);++sHeaderSerial;
}
static void FlushHeader(U16 page)
{
    if(sPageHeader[page]!=sHeaderSerial){
        sGraphicPos p={0,16};sGraphicRect r={0,16,320,8};
        Screen_Logic_Blit(&p,&r,Screen_GetpBackGraphic());sPageHeader[page]=sHeaderSerial;
    }
}
static void Reset(void)
{
    U16 page;sGraphicCanvas canvas=*Screen_GetpLogicGraphic();
    for(page=0;page<2;++page){
        canvas.mpVRAM=gScreenClass.mpBuffers[page];canvas.mpFuncs->CopyScreen(&canvas,Screen_GetpBack());
        Target(page);Dw_Show();gDwPrevious[page]=Dw_Zero;gDwPreviousMask[page]=0;sPageHeader[page]=sHeaderSerial;
    }
}
S16 GodLib_Game_Main(S16 argc,char **argv)
{
    U16 quit=0;U32 last=0;sGraphicCanvas *back;
    (void)argc;(void)argv;GemDos_Super(0);Platform_Init();
    Screen_Init(320,200,eGRAPHIC_COLOURMODE_4PLANE,0);
    if(!gScreenClass.mpMemBase){Platform_DeInit();return 1;}
    Graphic_SetBlitterEnable(0);back=Screen_GetpBackGraphic();GraphicCanvas_ClearScreen(back);
    Font8x8_PrintColourCanvas("DCK WAVE / LIVE 68000",back,80,0,14);
    Font8x8_PrintColourCanvas("1 ALL  2 ONE PLANE  3 TWO PLANES",back,0,8,14);
    Font8x8_PrintColourCanvas("SPACE PAUSE   N STEP   R CPU STRIPE",back,0,184,14);
    Font8x8_PrintColourCanvas("8PX WAVE / NO FRAME CACHE  ESC EXIT",back,0,192,14);
    Header();Reset();Video_SetPalST(Dw_Palette);gDwReady=1;
    while(!quit){
#ifdef DW_BENCH
        if(gDwHold){
            if(gDwRequest){
                U16 request=gDwRequest,n,count=request==2?512:1;gDwRequest=0;gDwCalls=0;
                if(gDwReset){Reset();gDwTestPage=0;gDwReset=0;}
                for(n=0;n<count;++n){
                    Target(gDwTestPage);
                    if(request==2)Dw_Frame();else{Dw_Select();Dw_Draw();}
                    gDwTestPage^=1;++gDwCalls;
                }
                gDwCompleted=request;
            }
            continue;
        }
#endif
        Screen_Update();
        {U32 now=Vbl_GetCounter();if(last && now-last>1)gDwMissedVbl+=now-last-1;last=now;}
        IKBD_Update();
        while(IKBD_GetKbdBytesWaiting()){
            U8 k=IKBD_PopKbdByte();
            if(k==eIKBDSCAN_ESC)quit=1;
            if(k==eIKBDSCAN_SPACE)gDwPaused^=1;
            if(k==eIKBDSCAN_R)gDwRaster^=1;
            if(k==eIKBDSCAN_N){gDwPaused=1;gDwPhase=(gDwPhase+1)&255;}
            if(k>=eIKBDSCAN_1 && k<=eIKBDSCAN_3){gDwMode=k-eIKBDSCAN_1;gDwMask=Dw_Masks[gDwMode];Header();}
        }
        {U16 page=Screen_GetLogicIndex();Target(page);FlushHeader(page);}
        if(gDwRaster)*(volatile U16*)0xffff8240UL=0x070;
        Dw_Frame();
        if(gDwRaster)*(volatile U16*)0xffff8240UL=0;
        ++gDwFrames;
    }
    Screen_DeInit();Platform_DeInit();gDwExited=1;return 0;
}
