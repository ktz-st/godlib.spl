#include <godlib/gemdos/gemdos.h>
#include <godlib/ikbd/ikbd.h>
#include <godlib/platform/platform.h>
#include <godlib/screen/screen.h>
#include <godlib/vbl/vbl.h>
#include <godlib/video/video.h>
extern void Wobble_Draw(void);
extern U16 Wobble_Picture[],Wobble_Lookup[];
U8 *gWobbleScreen;
U16 *gWobbleCursor,*gWobbleOldCursor,*gWobbleHistory[2];
volatile U16 gWobbleReady,gWobbleExited,gWobblePaused,gWobblePhase;
volatile U16 gWobbleAmplitude=8,gWobbleSpeed=8,gWobbleFramePhase,gWobbleFrameAmplitude;
volatile U32 gWobbleFrames,gWobbleLastVbl;
static void __attribute__((noinline)) Commands(void)
{
    U16 bank=0;
    gWobbleFramePhase=gWobblePhase;gWobbleFrameAmplitude=gWobbleAmplitude;
    switch(gWobbleAmplitude){case 4:bank=1;break;case 8:bank=2;break;case 16:bank=3;break;}
    gWobbleCursor=Wobble_Lookup+(U32)bank*768+gWobblePhase+398;
}
S16 GodLib_Game_Main(S16 argc,char **argv)
{
    U16 quit=0;
    (void)argc;(void)argv;GemDos_Super(0);Platform_Init();
    Screen_Init(320,200,eGRAPHIC_COLOURMODE_4PLANE,0);
    if(!gScreenClass.mpMemBase){Platform_DeInit();return 1;}
    Video_SetPalST(Wobble_Picture+1);Commands();
    gWobbleOldCursor=Wobble_Lookup+4*768+398; /* all $ffff: force first draw */
    gWobbleScreen=(U8*)Screen_GetpLogic();Wobble_Draw();
    gWobbleScreen=(U8*)Screen_GetpPhysic();Wobble_Draw();
    gWobbleHistory[0]=gWobbleHistory[1]=gWobbleCursor;
    gWobbleLastVbl=Vbl_GetCounter();gWobbleReady=1;
    while(!quit) {
        U32 now,elapsed;U16 page;
        Screen_Update();now=Vbl_GetCounter();elapsed=now-gWobbleLastVbl;
        gWobbleLastVbl=now;IKBD_Update();
        while(IKBD_GetKbdBytesWaiting()) {
            U8 k=IKBD_PopKbdByte();
            if(k==eIKBDSCAN_ESC)quit=1;
            if(k==eIKBDSCAN_SPACE)gWobblePaused^=1;
            if(k==eIKBDSCAN_0)gWobbleAmplitude=0;
            if(k==eIKBDSCAN_1)gWobbleAmplitude=4;
            if(k==eIKBDSCAN_2)gWobbleAmplitude=8;
            if(k==eIKBDSCAN_3)gWobbleAmplitude=16;
            if(k==eIKBDSCAN_S)gWobbleSpeed=gWobbleSpeed==16?4:gWobbleSpeed*2;
        }
        /* Motion follows real VBL time, including an occasional missed frame. */
        if(!gWobblePaused)gWobblePhase=(gWobblePhase+gWobbleSpeed*elapsed)&255;
        Commands();page=Screen_GetLogicIndex();
        gWobbleOldCursor=gWobbleHistory[page];gWobbleHistory[page]=gWobbleCursor;
        gWobbleScreen=(U8*)Screen_GetpLogic();Wobble_Draw();++gWobbleFrames;
    }
    Screen_DeInit();Platform_DeInit();gWobbleExited=1;return 0;
}
