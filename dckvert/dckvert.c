#include <godlib/gemdos/gemdos.h>
#include <godlib/graphic/graphic.h>
#include <godlib/font8x8/font8x8.h>
#include <godlib/ikbd/ikbd.h>
#include <godlib/platform/platform.h>
#include <godlib/screen/screen.h>
#include <godlib/vbl/vbl.h>
#include <godlib/video/video.h>
extern void Vert_Init(void),Vert_Advance(void),Vert_Draw(void);
extern U16 Vert_Palette[];
U32 gVertRows[3][288];
U8 gVertState[3*16];
U8 *gVertScreen;
volatile U16 gVertReady,gVertExited,gVertPaused,gVertRaster,gVertCount=3;
volatile U32 gVertFrames,gVertMissedVbl,gVertVbl;
#ifdef VERT_BENCH
volatile U16 gVertRequest,gVertCompleted,gVertHold;
volatile U32 gVertCalls;
#endif
static void Background(sGraphicCanvas *c)
{
    GraphicCanvas_ClearScreen(c);
    Font8x8_PrintColourCanvas("DCK VERTICAL - BIG 40X32",c,64,2,15);
    Font8x8_PrintColourCanvas("GODLIB",c,44,17,6);
    Font8x8_PrintColourCanvas("ATARI",c,144,17,6);
    Font8x8_PrintColourCanvas("DCK",c,248,17,6);
    Font8x8_PrintColourCanvas("1 PIXEL PER FRAME - FOUR BITPLANES",c,28,178,6);
    Font8x8_PrintColourCanvas("1/2/3 COLUMNS  SPACE PAUSE  R CPU  ESC",c,0,190,15);
}
S16 GodLib_Game_Main(S16 argc,char **argv)
{
    U16 quit=0,page,dirty[2]={0,0};U32 last=0;
    (void)argc;(void)argv;GemDos_Super(0);Platform_Init();
    Screen_Init(320,200,eGRAPHIC_COLOURMODE_4PLANE,0);
    if(!gScreenClass.mpMemBase){Platform_DeInit();return 1;}
    Vert_Init();Background(Screen_GetpLogicGraphic());Background(Screen_GetpPhysicGraphic());
    Video_SetPalST(Vert_Palette);gVertReady=1;
    while(!quit){
#ifdef VERT_BENCH
        if(gVertHold){
          if(gVertRequest){
            U16 n;gVertCount=gVertRequest;gVertRequest=0;gVertCalls=0;
            for(n=0;n<32;++n){Vert_Advance();Vert_Draw();++gVertCalls;}
            gVertCompleted=gVertCount;
          }
          continue;
        }
#endif
        Screen_Update();
        {U32 now=Vbl_GetCounter();if(last && now-last>1)gVertMissedVbl+=now-last-1;last=now;gVertVbl=now;}
        IKBD_Update();
        while(IKBD_GetKbdBytesWaiting()){
            U8 k=IKBD_PopKbdByte();
            if(k==eIKBDSCAN_ESC)quit=1;
            if(k==eIKBDSCAN_SPACE)gVertPaused^=1;
            if(k==eIKBDSCAN_R)gVertRaster^=1;
            if(k>=eIKBDSCAN_1 && k<=eIKBDSCAN_3){gVertCount=k-eIKBDSCAN_1+1;dirty[0]=dirty[1]=1;}
        }
        page=Screen_GetLogicIndex();
        if(dirty[page]){Background(Screen_GetpLogicGraphic());dirty[page]=0;}
        gVertScreen=(U8*)Screen_GetpLogic();
        if(gVertRaster)*(volatile U16*)0xffff8240UL=0x070;
        if(!gVertPaused)Vert_Advance();
        Vert_Draw();
        if(gVertRaster)*(volatile U16*)0xffff8240UL=0;
        ++gVertFrames;
    }
    Screen_DeInit();Platform_DeInit();gVertExited=1;return 0;
}
