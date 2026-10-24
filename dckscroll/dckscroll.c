#include <godlib/gemdos/gemdos.h>
#include <godlib/graphic/graphic.h>
#include <godlib/font8x8/font8x8.h>
#include <godlib/ikbd/ikbd.h>
#include <godlib/platform/platform.h>
#include <godlib/screen/screen.h>
#include <godlib/vbl/vbl.h>
#include <godlib/video/video.h>
extern void Dck_Init(void),Dck_Advance(void),Dck_Draw(void);
extern U16 Dck_Palette[];
U16 gDckCode[3*3881];
U32 gDckColumns[3][80];
U8 gDckState[3*16];
U8 *gDckScreen;
volatile U16 gDckReady,gDckExited,gDckPaused,gDckRaster,gDckCount=3;
volatile U32 gDckFrames,gDckMissedVbl,gDckVbl;
#ifdef DCK_BENCH
volatile U16 gDckRequest,gDckCompleted,gDckHold;
volatile U32 gDckCalls;
#endif
static void Background(sGraphicCanvas *c)
{
    GraphicCanvas_ClearScreen(c);
    Font8x8_PrintColourCanvas("DCK MULTISCROLL - BIG 40X32",c,48,2,15);
    Font8x8_PrintColourCanvas("SINE",c,0,14,6);
    Font8x8_PrintColourCanvas("ARCH",c,0,71,6);
    Font8x8_PrintColourCanvas("ZIGZAG",c,0,126,6);
    Font8x8_PrintColourCanvas("1/2/3 LANES  SPACE PAUSE  R CPU  ESC",c,0,190,15);
}
S16 GodLib_Game_Main(S16 argc,char **argv)
{
    U16 quit=0,page,dirty[2]={0,0};U32 last=0;
    (void)argc;(void)argv;GemDos_Super(0);Platform_Init();
    Screen_Init(320,200,eGRAPHIC_COLOURMODE_4PLANE,0);
    if(!gScreenClass.mpMemBase){Platform_DeInit();return 1;}
    Dck_Init();Background(Screen_GetpLogicGraphic());Background(Screen_GetpPhysicGraphic());
    Video_SetPalST(Dck_Palette);gDckReady=1;
    while(!quit){
#ifdef DCK_BENCH
        if(gDckHold){
          if(gDckRequest){
            U16 n;gDckCount=gDckRequest;gDckRequest=0;gDckCalls=0;
            for(n=0;n<32;++n){Dck_Advance();Dck_Draw();++gDckCalls;}
            gDckCompleted=gDckCount;
          }
          continue;
        }
#endif
        Screen_Update();
        {U32 now=Vbl_GetCounter();if(last && now-last>1)gDckMissedVbl+=now-last-1;last=now;gDckVbl=now;}
        IKBD_Update();
        while(IKBD_GetKbdBytesWaiting()){
            U8 k=IKBD_PopKbdByte();
            if(k==eIKBDSCAN_ESC)quit=1;
            if(k==eIKBDSCAN_SPACE)gDckPaused^=1;
            if(k==eIKBDSCAN_R)gDckRaster^=1;
            if(k>=eIKBDSCAN_1 && k<=eIKBDSCAN_3){gDckCount=k-eIKBDSCAN_1+1;dirty[0]=dirty[1]=1;}
        }
        page=Screen_GetLogicIndex();
        if(dirty[page]){Background(Screen_GetpLogicGraphic());dirty[page]=0;}
        gDckScreen=(U8*)Screen_GetpLogic();
        if(gDckRaster)*(volatile U16*)0xffff8240UL=0x070;
        if(!gDckPaused)Dck_Advance();
        Dck_Draw();
        if(gDckRaster)*(volatile U16*)0xffff8240UL=0;
        ++gDckFrames;
    }
    Screen_DeInit();Platform_DeInit();gDckExited=1;return 0;
}
