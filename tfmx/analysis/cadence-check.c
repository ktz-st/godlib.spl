#include <godlib/music/tfmx.h>
#include <godlib/file/file.h>
#include <godlib/platform/platform.h>
#include <godlib/screen/screen.h>
#include <godlib/system/system.h>
#include <godlib/gemdos/gemdos.h>
#include <godlib/ikbd/ikbd.h>
#include <godlib/vbl/vbl.h>
extern U16 renderingBlock;
extern volatile U32 gTfmxTicks;
volatile U16 gDone,gPass,gCase,gVideoMode,gVideoSync;
volatile U32 gCadVbl[2],gSeq[2],gMix[2],gSkippedSeq[2];
static void tick(void){U16 block=renderingBlock;U32 seq=gTfmxTicks;
 Tfmx_Tick();++gCadVbl[gCase];gSeq[gCase]+=gTfmxTicks-seq;
 if(block!=renderingBlock)++gMix[gCase];else gSkippedSeq[gCase]+=gTfmxTicks-seq;
}
static U16 run(void){sTfmxSong *s=Tfmx_Load("SOUNDS.MDT","SOUNDS.SMP",1);U16 sr;
 if(!s)return 0;
 for(gCase=0;gCase<2;++gCase){if(!Tfmx_Start(s,0,gCase+1)){Tfmx_UnLoad(s);return 0;}
 sr=System_GetIML();System_SetIML(7);Vbl_RemoveCall(Tfmx_Tick);Tfmx_SetSubSong(0);Vbl_AddCall(tick);System_SetIML(sr);
 while(gCadVbl[gCase]<1000)__asm__ volatile("nop":::"memory");
 sr=System_GetIML();System_SetIML(7);Vbl_RemoveCall(tick);System_SetIML(sr);Tfmx_Stop();}
 Tfmx_UnLoad(s);return gSeq[0]==gMix[0] && gSeq[1]==gMix[1] && !gSkippedSeq[0] && !gSkippedSeq[1];}
S16 GodLib_Game_Main(S16 a,char**b){(void)a;(void)b;GemDos_Super(0);Platform_Init();File_Init();Screen_Init(320,200,eGRAPHIC_COLOURMODE_4PLANE,0);gVideoMode=*(volatile U8*)0xffff8260UL;gVideoSync=*(volatile U8*)0xffff820aUL;gPass=run();gDone=1;while(!IKBD_GetKeyStatus(eIKBDSCAN_ESC))Screen_Update();Screen_DeInit();File_DeInit();Platform_DeInit();return 0;}
