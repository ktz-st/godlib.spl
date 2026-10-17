#include <godlib/gemdos/gemdos.h>
#include <godlib/ikbd/ikbd.h>
#include <godlib/platform/platform.h>
#include <godlib/screen/screen.h>
#include <godlib/vbl/vbl.h>
#include <godlib/video/video.h>
extern void Flag_Prepare(void),Flag_Draw(void),Flag_MouseShift(void);
extern U16 Flag_Palette[];
extern S16 Flag_Sine[];
S16 gFlagMouseOffsets[21],gFlagFrameOffsets[20],gFlagOld[2][20];
S16 *gFlagOldOffsets,*gFlagSine;
U8 *gFlagScreen;
volatile U16 gFlagReady,gFlagExited,gFlagPaused,gFlagMode=1;
volatile U16 gFlagPhase,gFlagAmplitude=1,gFlagSpeed=2,gFlagFramePhase,gFlagFrameMode;
volatile S16 gFlagMouseInput;
volatile U32 gFlagFrames,gFlagLastVbl;
S16 GodLib_Game_Main(S16 argc,char **argv)
{
    U16 quit=0,i,j;U32 last;
    (void)argc;(void)argv;GemDos_Super(0);Platform_Init();
    Screen_Init(320,200,eGRAPHIC_COLOURMODE_4PLANE,0);
    if(!gScreenClass.mpMemBase){Platform_DeInit();return 1;}
    Video_SetPalST(Flag_Palette);IKBD_EnableMouse();IKBD_SetMousePosition(160,100);
    for(i=0;i<2;++i)for(j=0;j<20;++j)gFlagOld[i][j]=32767;
    last=Vbl_GetCounter();gFlagLastVbl=last;gFlagReady=1;
    while(!quit) {
        U16 step=0;U32 now,elapsed;S16 mouse;
        Screen_Update();now=Vbl_GetCounter();elapsed=now-last;last=now;gFlagLastVbl=now;
        IKBD_Update();
        while(IKBD_GetKbdBytesWaiting()) {
            U8 k=IKBD_PopKbdByte();
            if(k==eIKBDSCAN_ESC)quit=1;
            if(k==eIKBDSCAN_SPACE)gFlagPaused^=1;
            if(k==eIKBDSCAN_M)gFlagMode=0;
            if(k==eIKBDSCAN_A)gFlagMode=1;
            if(k==eIKBDSCAN_N){gFlagPaused=1;step=1;}
            if(k>=eIKBDSCAN_1 && k<=eIKBDSCAN_3)gFlagAmplitude=k-eIKBDSCAN_1;
            if(k==eIKBDSCAN_S)gFlagSpeed=gFlagSpeed==8?2:gFlagSpeed*2;
        }
        mouse=IKBD_GetMouseY();if(mouse<0)mouse=0;if(mouse>199)mouse=199;
        gFlagMouseInput=(mouse-100)/10;
        if(gFlagMode && (!gFlagPaused || step))
            gFlagPhase=(gFlagPhase+(step?1:(U16)elapsed)*gFlagSpeed)&255;
        gFlagSine=Flag_Sine+(gFlagAmplitude<<8);
        gFlagOldOffsets=gFlagOld[Screen_GetLogicIndex()];gFlagScreen=(U8*)Screen_GetpLogic();
        gFlagFrameMode=gFlagMode;gFlagFramePhase=gFlagPhase;
        Flag_Prepare();Flag_Draw();++gFlagFrames;
        if(!gFlagMode && (!gFlagPaused || step))Flag_MouseShift();
    }
    Screen_DeInit();Platform_DeInit();gFlagExited=1;return 0;
}
