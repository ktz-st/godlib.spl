/* Native regression: IRQ audio while foreground deliberately does no rendering. */
#include <godlib/music/leonardmod.h>
#include <godlib/platform/platform.h>
#include <godlib/screen/screen.h>
#include <godlib/vbl/vbl.h>
#include <godlib/system/system.h>
#include <godlib/ikbd/ikbd.h>
#include <godlib/gemdos/gemdos.h>
#include <godlib/font8x8/font8x8.h>
#include <godlib/fade/fade.h>
#include <godlib/memory/memory.h>
#include <stdio.h>
volatile U16 gLeoTestDone,gLeoTestPass,gLeoTestStage,gLeoBadMask;
volatile U32 gLeoTicks,gLeoHoldTicks[2],gLeoHoldVbls[2],gLeoPcmNonzero[2],gLeoPcmChanges[2];
static S8 pcm[dMODSCOPE_STEREO_BYTES];
#define CHECK(expr,id) do{gLeoTestStage=id;if(!(expr))goto fail;}while(0)
static void audio(void)
{
 U16 before=System_GetIML();LeonardMod_Tick();if(before!=System_GetIML())++gLeoBadMask;++gLeoTicks;
}
static U8 attach(void)
{U16 mask=System_GetIML();U8 ok;System_SetIML(7);ok=Vbl_AddCall(audio);System_SetIML(mask);return ok;}
static void detach(void)
{U16 mask=System_GetIML();System_SetIML(7);Vbl_RemoveCall(audio);System_SetIML(mask);}
static U32 hash(void)
{U16 i;U32 value=0;LeonardMod_GetStereoOscilloscope(pcm);for(i=0;i<sizeof(pcm);++i)value=((value<<5)|(value>>27))^(U8)pcm[i];return value;}
static U16 run(void)
{
 U16 i,rate,mask,calls=Vbl_GetpVbl()->mCallCount,attached=0;U32 trap=*(volatile U32*)0x80,freeBefore=Memory_GetFree(),oldUsp,uspAfter,ticks,vbl,h,previous,stopTicks;void *mod=0;
 for(rate=1;rate<=2;++rate){
  mod=LeonardMod_Load("LOSTPARO.MOD");CHECK(mod,1+(rate-1)*9);
  CHECK(LeonardMod_Start(mod,(U8)rate),2+(rate-1)*9);
  CHECK(LeonardMod_GetPaulaAllocatedSize()==(rate==1?61134UL:91134UL),3+(rate-1)*9);
  CHECK(attach(),4+(rate-1)*9);attached=1;mask=System_GetIML();ticks=gLeoTicks;vbl=Vbl_GetCounter();
  __asm__ volatile("move.l %%usp,%0":"=a"(oldUsp));
  __asm__ volatile("move.l %0,%%usp"::"a"(0x12345678UL):"memory");
  /* IRQs remain enabled. No Screen_Update or foreground Tick for 64 VBLs. */
  while(gLeoTicks-ticks<64UL)__asm__ volatile("nop":::"memory");
  __asm__ volatile("move.l %%usp,%0":"=a"(uspAfter));
  __asm__ volatile("move.l %0,%%usp"::"a"(oldUsp):"memory");
  gLeoHoldTicks[rate-1]=gLeoTicks-ticks;gLeoHoldVbls[rate-1]=Vbl_GetCounter()-vbl;
  CHECK(uspAfter==0x12345678UL&&System_GetIML()==mask&&!gLeoBadMask,5+(rate-1)*9);
  CHECK(gLeoHoldTicks[rate-1]>=64&&gLeoHoldVbls[rate-1]+1>=gLeoHoldTicks[rate-1]&&gLeoHoldVbls[rate-1]<=gLeoHoldTicks[rate-1]+1,6+(rate-1)*9);
  previous=hash();for(i=0;i<sizeof(pcm);++i)if(pcm[i])++gLeoPcmNonzero[rate-1];
  for(i=0;i<4;++i){ticks=gLeoTicks;while(gLeoTicks-ticks<8)__asm__ volatile("nop":::"memory");h=hash();if(h!=previous)++gLeoPcmChanges[rate-1];previous=h;}
  CHECK(gLeoPcmNonzero[rate-1]>0&&gLeoPcmChanges[rate-1]>0,7+(rate-1)*9);
  detach();attached=0;stopTicks=gLeoTicks;LeonardMod_ShutdownPaula();Vbl_WaitVbls(3);
  CHECK(gLeoTicks==stopTicks&&!( *(volatile U8*)0xffff8901UL&3)&&*(volatile U32*)0x80==trap&&!LeonardMod_GetPaulaAllocatedSize(),8+(rate-1)*9);
  LeonardMod_UnLoad(mod);mod=0;CHECK(Vbl_GetpVbl()->mCallCount==calls&&Memory_GetFree()==freeBefore,9+(rate-1)*9);
 }
 return 1;
fail:
 if(attached)detach();
 LeonardMod_ShutdownPaula();
 if(mod)LeonardMod_UnLoad(mod);
 return 0;
}
S16 GodLib_Game_Main(S16 argc,char **argv)
{
 U16 dirty=2;char line[40];static U16 pal[16]={0,0x777};(void)argc;(void)argv;
 GemDos_Super(0);Platform_Init();Screen_Init(320,200,eGRAPHIC_COLOURMODE_4PLANE,0);Fade_SetPalDirect(pal);
 gLeoTestPass=run();gLeoTestDone=1;
 while(!IKBD_GetKeyStatus(eIKBDSCAN_ESC)){Screen_Update();if(dirty){Screen_Logic_ClearScreen();sprintf(line,"LEONARD VBL %s / CHECK %u",gLeoTestPass?"PASS":"FAIL",gLeoTestStage);Font8x8_Print(line,Screen_GetpLogic(),0,16);--dirty;}}
 Screen_DeInit();Platform_DeInit();return !gLeoTestPass;
}
