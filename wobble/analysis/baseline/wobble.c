#include <godlib/gemdos/gemdos.h>
#include <godlib/ikbd/ikbd.h>
#include <godlib/platform/platform.h>
#include <godlib/screen/screen.h>
#include <godlib/vbl/vbl.h>
#include <godlib/video/video.h>
#include "assets/sine.h"
extern void Wobble_Draw(void);
extern U16 Wobble_Picture[];
U8 *gWobbleScreen;
U16 gWobbleCommands[200][3];
S16 gWobbleOffsets[200];
volatile U16 gWobbleReady,gWobbleExited,gWobblePaused,gWobblePhase;
volatile U16 gWobbleAmplitude=8,gWobbleSpeed=2,gWobbleFramePhase,gWobbleFrameAmplitude;
volatile U32 gWobbleFrames,gWobbleLastVbl;
static void Commands(void)
{
    U16 y;gWobbleFramePhase=gWobblePhase;gWobbleFrameAmplitude=gWobbleAmplitude;
    for(y=0;y<200;++y) {
        S16 dx=gSine[(gWobblePhase+y*2)&255];U16 start,fine;
        switch(gWobbleAmplitude) {
        case 0:dx=0;break;
        case 4:dx>>=2;break;
        case 8:dx>>=1;break;
        default:break;
        }
        gWobbleOffsets[y]=dx;
        start=16-dx;fine=start&15;
        gWobbleCommands[y][0]=(start>>4)*2;
        if(!fine){gWobbleCommands[y][1]=0;gWobbleCommands[y][2]=0;}
        else if(fine<=8){gWobbleCommands[y][1]=fine;gWobbleCommands[y][2]=1;}
        else{gWobbleCommands[y][1]=16-fine;gWobbleCommands[y][2]=2;}
    }
}
S16 GodLib_Game_Main(S16 argc,char **argv)
{
    U16 quit=0;
    (void)argc;(void)argv;GemDos_Super(0);Platform_Init();
    Screen_Init(320,200,eGRAPHIC_COLOURMODE_4PLANE,0);
    if(!gScreenClass.mpMemBase){Platform_DeInit();return 1;}
    Video_SetPalST(Wobble_Picture+1);Commands();
    gWobbleScreen=(U8*)Screen_GetpLogic();Wobble_Draw();
    gWobbleScreen=(U8*)Screen_GetpPhysic();Wobble_Draw();gWobbleReady=1;
    while(!quit) {
        Screen_Update();gWobbleLastVbl=Vbl_GetCounter();IKBD_Update();
        while(IKBD_GetKbdBytesWaiting()) {
            U8 k=IKBD_PopKbdByte();
            if(k==eIKBDSCAN_ESC)quit=1;
            if(k==eIKBDSCAN_SPACE)gWobblePaused^=1;
            if(k==eIKBDSCAN_0)gWobbleAmplitude=0;
            if(k==eIKBDSCAN_1)gWobbleAmplitude=4;
            if(k==eIKBDSCAN_2)gWobbleAmplitude=8;
            if(k==eIKBDSCAN_3)gWobbleAmplitude=16;
            if(k==eIKBDSCAN_S)gWobbleSpeed=gWobbleSpeed==4?1:gWobbleSpeed*2;
        }
        if(!gWobblePaused)gWobblePhase=(gWobblePhase+gWobbleSpeed)&255;
        Commands();gWobbleScreen=(U8*)Screen_GetpLogic();Wobble_Draw();++gWobbleFrames;
    }
    Screen_DeInit();Platform_DeInit();gWobbleExited=1;return 0;
}
