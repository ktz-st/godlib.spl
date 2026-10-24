#include <godlib/gemdos/gemdos.h>
#include <godlib/graphic/graphic.h>
#include <godlib/font8x8/font8x8.h>
#include <godlib/ikbd/ikbd.h>
#include <godlib/platform/platform.h>
#include <godlib/screen/screen.h>
#include <godlib/vbl/vbl.h>
#include <godlib/video/video.h>
extern void HS_Init(void),HS_Advance(void),HS_Draw(void);
extern U16 HS_Palette[];
U32 gHSColumns[1][80];
U8 gHSState[1*24];
U8 *gHSScreen;
volatile U16 gHSReady,gHSExited,gHSPaused,gHSRaster,gHSCount=1;
volatile U32 gHSFrames,gHSMissedVbl,gHSVbl;
#ifdef HS_BENCH
volatile U16 gHSRequest,gHSCompleted,gHSHold;
volatile U32 gHSCalls;
#endif
static void Background(sGraphicCanvas *c)
{
    GraphicCanvas_ClearScreen(c);
    sGraphicRect line;
    Font8x8_PrintColourCanvas("DCK HORIZONTAL SCROLLER",c,72,16,15);
    Font8x8_PrintColourCanvas("ESCALI 16X16 COLOUR FONT",c,64,40,6);
    line.mX=0;line.mWidth=320;line.mHeight=1;line.mY=80;GraphicCanvas_DrawBox(c,&line,6);
    line.mY=119;GraphicCanvas_DrawBox(c,&line,6);
    Font8x8_PrintColourCanvas("8 PIXELS EVERY 2 VBL",c,88,144,15);
    Font8x8_PrintColourCanvas("SPACE PAUSE   R CPU   ESC EXIT",c,40,184,15);
}
S16 GodLib_Game_Main(S16 argc,char **argv)
{
    U16 quit=0,page,dirty[2]={0,0};U32 last=0;
    (void)argc;(void)argv;GemDos_Super(0);Platform_Init();
    Screen_Init(320,200,eGRAPHIC_COLOURMODE_4PLANE,0);
    if(!gScreenClass.mpMemBase){Platform_DeInit();return 1;}
    HS_Init();Background(Screen_GetpLogicGraphic());Background(Screen_GetpPhysicGraphic());
    Video_SetPalST(HS_Palette);gHSReady=1;
    while(!quit){
#ifdef HS_BENCH
        if(gHSHold){
          if(gHSRequest){
            U16 n;gHSCount=gHSRequest;gHSRequest=0;gHSCalls=0;
            for(n=0;n<32;++n){HS_Advance();HS_Draw();++gHSCalls;}
            gHSCompleted=gHSCount;
          }
          continue;
        }
#endif
        Screen_Update();
        {U32 now=Vbl_GetCounter();if(last && now-last>1)gHSMissedVbl+=now-last-1;last=now;gHSVbl=now;}
        IKBD_Update();
        while(IKBD_GetKbdBytesWaiting()){
            U8 k=IKBD_PopKbdByte();
            if(k==eIKBDSCAN_ESC)quit=1;
            if(k==eIKBDSCAN_SPACE)gHSPaused^=1;
            if(k==eIKBDSCAN_R)gHSRaster^=1;
            if(k>=eIKBDSCAN_1 && k<=eIKBDSCAN_1){gHSCount=k-eIKBDSCAN_1+1;dirty[0]=dirty[1]=1;}
        }
        page=Screen_GetLogicIndex();
        if(dirty[page]){Background(Screen_GetpLogicGraphic());dirty[page]=0;}
        gHSScreen=(U8*)Screen_GetpLogic();
        if(gHSRaster)*(volatile U16*)0xffff8240UL=0x070;
        if(!gHSPaused)HS_Advance();
        HS_Draw();
        if(gHSRaster)*(volatile U16*)0xffff8240UL=0;
        ++gHSFrames;
    }
    Screen_DeInit();Platform_DeInit();gHSExited=1;return 0;
}
