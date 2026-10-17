#include <godlib/gemdos/gemdos.h>
#include <godlib/ikbd/ikbd.h>
#include <godlib/memory/memory.h>
#include <godlib/platform/platform.h>
#include <godlib/screen/screen.h>
#include <godlib/vbl/vbl.h>
#include <godlib/video/video.h>
#include <godlib/graphic/reflection.h>
extern U16 Reflect_Picture[];
extern U8 Reflect_Source[];
sGraphicReflect gReflection;
volatile U16 gReflectReady,gReflectExited,gReflectPaused,gReflectTick;
volatile U16 gReflectFrameTick;
volatile U32 gReflectFrames,gReflectLastVbl;
S16 GodLib_Game_Main(S16 argc,char **argv)
{
    U16 quit=0;
    (void)argc;(void)argv;GemDos_Super(0);Platform_Init();
    Screen_Init(320,200,eGRAPHIC_COLOURMODE_4PLANE,0);
    if(!gScreenClass.mpMemBase){Platform_DeInit();return 1;}
    Memory_Copy(32000UL,(U8*)Reflect_Picture+34,Screen_GetpLogic());
    Memory_Copy(32000UL,(U8*)Reflect_Picture+34,Screen_GetpPhysic());
    Video_SetPalST(Reflect_Picture+1);
    gReflection.mpSource=Reflect_Source;
    gReflection.mSourceY1=0;gReflection.mSourceY2=199;gReflection.mDestY=112;
    gReflectReady=1;
    while(!quit) {
        U16 step=0;
        Screen_Update();gReflectLastVbl=Vbl_GetCounter();IKBD_Update();
        while(IKBD_GetKbdBytesWaiting()) {
            U8 k=IKBD_PopKbdByte();
            if(k==eIKBDSCAN_ESC)quit=1;
            if(k==eIKBDSCAN_SPACE)gReflectPaused^=1;
            if(k==eIKBDSCAN_N){gReflectPaused=1;step=1;}
        }
        if(step && ++gReflectTick==40)gReflectTick=0;
        gReflectFrameTick=gReflectTick;
        /* Reconstitute input state so both pages show the same paused tick. */
        gReflection.mToggle=gReflectTick&1;
        gReflection.mPhase=(gReflectTick/2)*2;
        gReflection.mpDest=Screen_GetpLogic();
        Graphic_Reflect(&gReflection);++gReflectFrames;
        if(!gReflectPaused && ++gReflectTick==40)gReflectTick=0;
    }
    Screen_DeInit();Platform_DeInit();gReflectExited=1;return 0;
}
