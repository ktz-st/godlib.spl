#include <godlib/gemdos/gemdos.h>
#include <godlib/graphic/graphic.h>
#include <godlib/font8x8/font8x8.h>
#include <godlib/ikbd/ikbd.h>
#include <godlib/platform/platform.h>
#include <godlib/screen/screen.h>
#include <godlib/vbl/vbl.h>
#include <godlib/video/video.h>
extern void Route_Init(void),Route_Advance(void),Route_Frame(void);
extern U16 Route_Palette[];
U8 *gRouteScreen,*gRouteText;
U16 gRouteQueue[9],gRouteY[40],gRoutePreviousY[2][40],gRoutePreviousMode[2];
U32 gRouteColumnPtrs[45];
volatile U16 gRoutePage,gRouteMode,gRouteProfile,gRoutePhase,gRouteRequest;
volatile U16 gRouteReady,gRouteExited,gRoutePaused,gRouteRaster;
volatile U32 gRouteFrames,gRouteMissedVbl,gRouteCommands;
#ifdef ROUTE_BENCH
volatile U16 gRouteHold,gRouteBenchRequest,gRouteCompleted;
volatile U32 gRouteCalls;
static U8 sBenchPages[2][32000];
#endif
static void Background(sGraphicCanvas *c)
{
    GraphicCanvas_ClearScreen(c);
    Font8x8_PrintColourCanvas("DCK ROUTE - ONE TEXT, MANY PATHS",c,40,2,15);
    Font8x8_PrintColourCanvas("N NEXT   P/H/V MODE   0-9 PROFILE",c,0,184,15);
    Font8x8_PrintColourCanvas("SPACE PAUSE    R CPU    ESC EXIT",c,0,192,15);
}
static void Caption(sGraphicCanvas *c)
{
    static const char *names[]={"CURVE  ","STRIP  ","COLUMN "};
    char label[]="P0";
    label[0]="PHV"[gRouteMode];label[1]='0'+gRouteProfile;
    Font8x8_PrintColourCanvas(names[gRouteMode],c,0,14,6);
    Font8x8_PrintColourCanvas(label,c,248,14,15);
}
S16 GodLib_Game_Main(S16 argc,char **argv)
{
    static const U16 sequence[]={3,8,5,11,12,1,10};
    U16 quit=0,select=0;U32 last=0;
    (void)argc;(void)argv;GemDos_Super(0);Platform_Init();
    Screen_Init(320,200,eGRAPHIC_COLOURMODE_4PLANE,0);
    if(!gScreenClass.mpMemBase){Platform_DeInit();return 1;}
    Route_Init();Background(Screen_GetpLogicGraphic());Background(Screen_GetpPhysicGraphic());
    Video_SetPalST(Route_Palette);gRouteReady=1;
    while(!quit){
#ifdef ROUTE_BENCH
        if(gRouteHold){
            if(gRouteBenchRequest){
                U16 n,request=gRouteBenchRequest;gRouteBenchRequest=0;gRouteCalls=0;
                for(n=0;n<(request==1?1:128);++n){
                    gRoutePage^=1;gRouteScreen=sBenchPages[gRoutePage];
                    if(!gRoutePaused)Route_Advance();
                    Route_Frame();++gRouteCalls;
                }
                gRouteCompleted=request;
            }
            continue;
        }
#endif
        Screen_Update();
        {U32 now=Vbl_GetCounter();if(last && now-last>1)gRouteMissedVbl+=now-last-1;last=now;}
        IKBD_Update();
        while(IKBD_GetKbdBytesWaiting()){
            U8 k=IKBD_PopKbdByte();
            if(k==eIKBDSCAN_ESC)quit=1;
            if(k==eIKBDSCAN_SPACE)gRoutePaused^=1;
            if(k==eIKBDSCAN_R)gRouteRaster^=1;
            if(k==eIKBDSCAN_N){select=(select+1)%7;gRouteRequest=sequence[select];}
            if(k==eIKBDSCAN_P)gRouteRequest=gRouteProfile+1;
            if(k==eIKBDSCAN_H)gRouteRequest=11;
            if(k==eIKBDSCAN_V)gRouteRequest=12;
            if(k>=eIKBDSCAN_1 && k<=eIKBDSCAN_9)gRouteRequest=k-eIKBDSCAN_1+2;
            if(k==eIKBDSCAN_0)gRouteRequest=1;
        }
        gRoutePage=Screen_GetLogicIndex();gRouteScreen=(U8*)Screen_GetpLogic();
        if(gRouteRaster)*(volatile U16*)0xffff8240UL=0x070;
        if(!gRoutePaused)Route_Advance();
        Route_Frame();
        if(gRouteRaster)*(volatile U16*)0xffff8240UL=0;
        Caption(Screen_GetpLogicGraphic());++gRouteFrames;
    }
    Screen_DeInit();Platform_DeInit();gRouteExited=1;return 0;
}
