#include <godlib/gemdos/gemdos.h>
#include <godlib/font8x8/font8x8.h>
#include <godlib/graphic/graphic.h>
#include <godlib/ikbd/ikbd.h>
#include <godlib/platform/platform.h>
#include <godlib/screen/screen.h>
#include <godlib/vbl/vbl.h>
#include <godlib/video/video.h>
extern void Db_Init(void),Db_Frame(void),Db_Show(void);
extern U16 Db_Palette[];
U8 *gDbDest;
U16 gDbHistory[2][4],gDbCommands[11][7],gDbCount;
volatile U16 gDbMode,gDbMask=15,gDbPhase,gDbPaused,gDbRaster,gDbPage,gDbReady,gDbExited;
volatile U32 gDbFrames,gDbMissedVbl;
static U16 sHeaderSerial,sPageHeader[2];
#ifdef DB_BENCH
volatile U16 gDbHold,gDbRequest,gDbCompleted,gDbReset,gDbTestPage;
volatile U32 gDbCalls;
#endif
static void Target(U16 page){gDbPage=page;gDbDest=(U8*)gScreenClass.mpBuffers[page]+24*160;}
static void Header(void)
{
    static const char *names[]={"1 MOVE BLOCK 128X64","2 REPEAT SOURCE ROWS","3 SKIP SOURCE ROWS / X2","4 REVERSE DESTINATION / ROLL","5 REORDER 32X80 STRIPS"};
    const char *planes=gDbMask==15?"PLANES 0+1+2+3":gDbMask==2?"PLANE 1":"PLANES 0+2";
    sGraphicCanvas *c=Screen_GetpBackGraphic();sGraphicRect r={0,8,320,16};
    GraphicCanvas_DrawBox(c,&r,0);Font8x8_PrintColourCanvas(names[gDbMode],c,0,8,14);
    Font8x8_PrintColourCanvas(planes,c,0,16,14);++sHeaderSerial;
}
static void FlushHeader(U16 page)
{
    if(sPageHeader[page]!=sHeaderSerial){
        sGraphicPos p={0,8};sGraphicRect r={0,8,320,16};
        Screen_Logic_Blit(&p,&r,Screen_GetpBackGraphic());sPageHeader[page]=sHeaderSerial;
    }
}
static void Reset(void)
{
    U16 page;sGraphicCanvas canvas=*Screen_GetpLogicGraphic();Db_Init();
    for(page=0;page<2;++page){
        canvas.mpVRAM=gScreenClass.mpBuffers[page];canvas.mpFuncs->CopyScreen(&canvas,Screen_GetpBack());
        Target(page);Db_Show();sPageHeader[page]=sHeaderSerial;
    }
}
S16 GodLib_Game_Main(S16 argc,char **argv)
{
    U16 quit=0,maskIndex=0;U32 last=0;sGraphicCanvas *back;static const U16 masks[]={15,2,5};
    (void)argc;(void)argv;GemDos_Super(0);Platform_Init();
    Screen_Init(320,200,eGRAPHIC_COLOURMODE_4PLANE,0);
    if(!gScreenClass.mpMemBase){Platform_DeInit();return 1;}
    Graphic_SetBlitterEnable(0);back=Screen_GetpBackGraphic();GraphicCanvas_ClearScreen(back);
    Font8x8_PrintColourCanvas("DCK BLOCK COPY / LIVE 68000",back,56,0,14);
    Font8x8_PrintColourCanvas("1 MOVE 2 REPEAT 3 SKIP 4 FLIP 5 STRIPS",back,0,184,14);
    Font8x8_PrintColourCanvas("M PLANES SPACE PAUSE N STEP R CPU ESC",back,0,192,14);
    Header();Reset();Video_SetPalST(Db_Palette);gDbReady=1;
    while(!quit){
#ifdef DB_BENCH
        if(gDbHold){
            if(gDbRequest){
                U16 request=gDbRequest,n,count=request==2?320:1;gDbRequest=0;gDbCalls=0;
                if(gDbReset){Reset();gDbTestPage=0;gDbReset=0;}
                for(n=0;n<count;++n){Target(gDbTestPage);Db_Frame();gDbTestPage^=1;++gDbCalls;}
                gDbCompleted=request;
            }
            continue;
        }
#endif
        Screen_Update();
        {U32 now=Vbl_GetCounter();if(last&&now-last>1)gDbMissedVbl+=now-last-1;last=now;}
        IKBD_Update();
        while(IKBD_GetKbdBytesWaiting()){
            U8 k=IKBD_PopKbdByte();
            if(k==eIKBDSCAN_ESC)quit=1;
            if(k==eIKBDSCAN_SPACE)gDbPaused^=1;
            if(k==eIKBDSCAN_R)gDbRaster^=1;
            if(k==eIKBDSCAN_N){gDbPaused=1;gDbPhase=(gDbPhase+1)%160;}
            if(k==eIKBDSCAN_M){maskIndex=(maskIndex+1)%3;gDbMask=masks[maskIndex];Header();}
            if(k>=eIKBDSCAN_1&&k<=eIKBDSCAN_5){gDbMode=k-eIKBDSCAN_1;Header();}
        }
        {U16 page=Screen_GetLogicIndex();Target(page);FlushHeader(page);}
        if(gDbRaster)*(volatile U16*)0xffff8240UL=0x070;
        Db_Frame();
        if(gDbRaster)*(volatile U16*)0xffff8240UL=0;
        ++gDbFrames;
    }
    Screen_DeInit();Platform_DeInit();gDbExited=1;return 0;
}
