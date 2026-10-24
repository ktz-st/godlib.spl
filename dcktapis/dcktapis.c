#include "dcktapis.h"
#include <godlib/gemdos/gemdos.h>
#include <godlib/font8x8/font8x8.h>
#include <godlib/graphic/graphic.h>
#include <godlib/ikbd/ikbd.h>
#include <godlib/platform/platform.h>
#include <godlib/screen/screen.h>
#include <godlib/system/system.h>
#include <godlib/vbl/vbl.h>
#include <godlib/video/video.h>
#include <stdio.h>

U8 *gTpDest;
volatile U16 gTpControl=4,gTpLatched=4,gTpPhase,gTpCountdown=2,gTpAttached,gTpReady,gTpExited;
volatile U32 gTpTicks,gTpChanges,gTpFrames,gTpMissedVbl;
static U16 sHeaderSerial,sPageHeader[2];
#ifdef TP_BENCH
typedef struct {U32 tick;U16 phase,control,countdown,palette[16];} sTpRecord;
volatile sTpRecord gTpLog[512];
volatile U16 gTpLogCount,gTpHoldMain;
static void TraceVbl(void)
{
    U16 n=gTpLogCount,i;Tp_Vbl();
    if(n<512){
        gTpLog[n].tick=gTpTicks;gTpLog[n].phase=gTpPhase;gTpLog[n].control=gTpLatched;gTpLog[n].countdown=gTpCountdown;
        for(i=0;i<16;++i)gTpLog[n].palette[i]=((volatile U16*)0xffff8240UL)[i];
        gTpLogCount=n+1;
    }
}
#define TP_CALLBACK TraceVbl
#else
#define TP_CALLBACK Tp_Vbl
#endif
static void Header(void)
{
    U16 c=gTpControl;sGraphicCanvas *back=Screen_GetpBackGraphic();sGraphicRect r={0,80,320,8};char text[41];
    GraphicCanvas_DrawBox(back,&r,0);
    sprintf(text,"%s / %u VBL / %s",c&2?"REVERSE":"FORWARD",1U<<((c>>2)&3),c&1?"PAUSED":"PLAYING");
    Font8x8_PrintColourCanvas(text,back,0,80,1);++sHeaderSerial;
}
static void FlushHeader(U16 page)
{
    if(sPageHeader[page]!=sHeaderSerial){
        sGraphicPos p={0,80};sGraphicRect r={0,80,320,8};
        Screen_Logic_Blit(&p,&r,Screen_GetpBackGraphic());sPageHeader[page]=sHeaderSerial;
    }
}
S16 GodLib_Game_Main(S16 argc,char **argv)
{
    U16 quit=0,mask;U32 last=0;sGraphicCanvas *back;
    (void)argc;(void)argv;GemDos_Super(0);Platform_Init();
    Screen_Init(320,200,eGRAPHIC_COLOURMODE_4PLANE,0);
    if(!gScreenClass.mpMemBase){Platform_DeInit();return 1;}
    Graphic_SetBlitterEnable(0);back=Screen_GetpBackGraphic();gTpDest=(U8*)Screen_GetpBack();Tp_Show();
    Font8x8_PrintColourCanvas("DCK TAPIS / VBL PALETTE",back,72,64,1);
    Font8x8_PrintColourCanvas("1/2/3 SPEED  D REVERSE  SPACE PAUSE",back,0,184,1);
    Font8x8_PrintColourCanvas("N STEP                   ESC EXIT",back,0,192,1);
    Header();GraphicCanvas_CopyScreen(Screen_GetpLogicGraphic(),Screen_GetpBack());
    GraphicCanvas_CopyScreen(Screen_GetpPhysicGraphic(),Screen_GetpBack());sPageHeader[0]=sPageHeader[1]=sHeaderSerial;
    Video_SetPalST(Tp_Palettes);
    mask=System_GetIML();System_SetIML(7);gTpAttached=Vbl_AddCall(TP_CALLBACK);System_SetIML(mask);
    if(!gTpAttached)goto done;
    gTpReady=1;
    while(!quit){
#ifdef TP_BENCH
        if(gTpHoldMain)continue; /* Verification: palettes keep moving in VBL. */
#endif
        Screen_Update();
        {U32 now=Vbl_GetCounter();if(last && now-last>1)gTpMissedVbl+=now-last-1;last=now;}
        IKBD_Update();
        while(IKBD_GetKbdBytesWaiting()){
            U8 k=IKBD_PopKbdByte();U16 c=gTpControl;
            if(k==eIKBDSCAN_ESC)quit=1;
            if(k==eIKBDSCAN_SPACE)c^=1;
            if(k==eIKBDSCAN_D)c^=2;
            if(k==eIKBDSCAN_N){c|=1;c^=16;}
            if(k>=eIKBDSCAN_1 && k<=eIKBDSCAN_3)c=(c&~12)|((k-eIKBDSCAN_1)<<2);
            if(c!=gTpControl){gTpControl=c;Header();}
        }
        FlushHeader(Screen_GetLogicIndex());++gTpFrames;
    }
done:
    mask=System_GetIML();System_SetIML(7);
    if(gTpAttached){Vbl_RemoveCall(TP_CALLBACK);gTpAttached=0;}
    System_SetIML(mask);Screen_DeInit();Platform_DeInit();gTpExited=1;return 0;
}
