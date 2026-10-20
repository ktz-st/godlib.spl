/* Native regression against the original VectorDean sequencer, plus lifecycle. */
#include <godlib/music/rjp1.h>
#include <godlib/music/lancemod.h>
#include <godlib/music/paulamixer.h>
#include <godlib/file/file.h>
#include <godlib/memory/memory.h>
#include <godlib/gemdos/gemdos.h>
#include <godlib/platform/platform.h>
#include <godlib/screen/screen.h>
#include <godlib/vbl/vbl.h>
#include <godlib/system/system.h>
#include <godlib/ikbd/ikbd.h>
#include <string.h>
extern void vd_init(void *song,void *ins),vd_start_song(U16 song),vd_tick(void);
extern void RjpCore_Tick(void);
extern void RjpTest_Arm(void*,void*,U16,U16,U16);
extern void vd_translate_init(void),vd_translate(void);
extern U8 fake_dff_base[];
volatile U16 gTestDone,gTestPass,gTestStage,gTestBank,gTestSong,gTestChannel,gTestWant,gTestGot;
volatile U32 gTestTicks,gTestCompared,gTestFreeBefore,gTestFreeAfter,gTestResident[2];
static void marker(void){++gTestTicks;}
#define CHECK(x,n) do{gTestStage=n;if(!(x))goto fail;}while(0)
static U16 run(void)
{
 const char *sng[2]={"JON.SNG","WARX4.SNG"},*ins[2]={"JON.INS","WARX4.INS"};
 U16 b,sub,t,ch,rate,mask,calls=Vbl_GetpVbl()->mCallCount,added=0;U32 trap=*(volatile U32*)0x80,ticks,vbl,usp,before,after;void *s=0,*i=0,*mod=0;sRjp1Song *song=0;sRjp1Info info;
 {U32 voice[5],pcm[16];
  memset(voice,0x55,sizeof(voice));RjpTest_Arm(voice,pcm,4,1,0);
  CHECK(voice[0]==(U32)pcm && voice[1]==(U32)pcm+8 && !voice[2] && !*(U16*)((U8*)voice+16),21);
  voice[0]+=6;RjpTest_Arm(voice,pcm,4,1,0);CHECK(voice[0]==(U32)pcm,22);
  RjpTest_Arm(voice,pcm,4,2,2);CHECK(voice[1]==(U32)pcm+8 && voice[2]==(U32)pcm+4,23);
  RjpTest_Arm(voice,pcm,4,2,4);CHECK(voice[1]==(U32)pcm+12 && voice[2]==(U32)pcm+8,24);
 }
 gTestFreeBefore=Memory_GetFree();
 CHECK(!Rjp1_Create(0,0,0,0),1);
 for(b=0;b<2;++b){gTestBank=b;
  s=File_Load(sng[b]);i=File_Load(ins[b]);CHECK(s&&i,2);
  song=Rjp1_Create(s,File_GetSize(sng[b]),i,File_GetSize(ins[b]));CHECK(song,3);
  Rjp1_GetInfo(song,&info);gTestResident[b]=info.mResidentBytes;
  CHECK(!Rjp1_Start(song,info.mSubSongs,2),4);
  for(sub=0;sub<info.mSubSongs;++sub){gTestSong=sub;
   /* Original mutates records, so reload the original pair each subsong. */
   File_UnLoad(s);File_UnLoad(i);s=File_Load(sng[b]);i=File_Load(ins[b]);CHECK(s&&i,5);
   {U16 z;for(z=0;z<256;++z)fake_dff_base[z]=0;}
   vd_init(s,i);vd_start_song(sub);vd_translate_init();
   /* Keep IRQs masked through Start AND detachment: otherwise Start can
      run one asynchronous tick before the deterministic comparison begins. */
   {U8 started;mask=System_GetIML();System_SetIML(7);
    started=Rjp1_Start(song,sub,1);Vbl_RemoveCall(Rjp1_Tick);System_SetIML(mask);
    CHECK(started,6);
   }
   /* Do not mix here: compare native sequence/envelope/period arithmetic.
      PCM boundaries/retrigger behavior are deliberately corrected separately. */
   for(t=0;t<3000;++t){
    {U8 saved[80];memcpy(saved,PaulaMixer_Channels,80);vd_tick();vd_translate();memcpy(PaulaMixer_Channels,saved,80);RjpCore_Tick();}
    for(ch=0;ch<4;++ch){U8 *a=fake_dff_base+0xa0+16*ch,*c=PaulaMixer_Channels+20*ch;
     gTestChannel=ch;gTestWant=*(U16*)(a+8);gTestGot=*(U16*)(c+12);
     CHECK(gTestWant==gTestGot,7);
     gTestWant=*(U16*)(a+6);if(gTestWant>907)gTestWant=907;gTestGot=*(U16*)(c+14);
     CHECK(gTestWant==gTestGot,8);
    }
    ++gTestCompared;
   }
   Rjp1_Stop();
  }
  File_UnLoad(s);s=0;File_UnLoad(i);i=0;
  for(rate=1;rate<=3;++rate){
   CHECK(Rjp1_Start(song,1,(U8)rate),9);
   CHECK(Rjp1_GetAllocatedSize()==Rjp1_GetWorkspaceSize((U8)rate),10);
   CHECK(!PaulaMixer_Init(1,2),11); /* active RJP owner is protected */
   mask=System_GetIML();System_SetIML(7);added=Vbl_AddCall(marker);System_SetIML(mask);CHECK(added,12);
   ticks=gTestTicks;vbl=Vbl_GetCounter();before=System_GetIML();
   __asm__ volatile("move.l %%usp,%0":"=a"(usp));__asm__ volatile("move.l %0,%%usp"::"a"(0x12345678UL):"memory");
   while(gTestTicks-ticks<64)__asm__ volatile("nop":::"memory");
   __asm__ volatile("move.l %%usp,%0":"=a"(after));__asm__ volatile("move.l %0,%%usp"::"a"(usp):"memory");
   CHECK(after==0x12345678UL&&System_GetIML()==before&&Vbl_GetCounter()-vbl>=64,13);
   mask=System_GetIML();System_SetIML(7);Vbl_RemoveCall(marker);System_SetIML(mask);added=0;
   CHECK(Rjp1_SetSubSong(1),14);Rjp1_SetVolume(0);Vbl_WaitVbls(2);Rjp1_SetVolume(64);
   Rjp1_Stop();CHECK(!Rjp1_GetAllocatedSize()&&*(U32*)0x80==trap&&!(*(U8*)0xffff8901UL&3),15);
  }
  CHECK(Rjp1_Start(song,1,2),16);Rjp1_UnLoad(song);song=0;
  CHECK(Vbl_GetpVbl()->mCallCount==calls&&!Rjp1_GetAllocatedSize(),17);
 }
 /* Shared backend must still run ProTracker after RJP has released it. */
 mod=LanceMod_Load("LOSTPARO.MOD");CHECK(mod,18);
 for(rate=1;rate<=3;++rate){CHECK(LanceMod_Start(mod,(U8)rate),19);Vbl_WaitVbls(8);LanceMod_ShutdownPaula();}
 LanceMod_UnLoad(mod);mod=0;
 gTestFreeAfter=Memory_GetFree();CHECK(gTestFreeAfter==gTestFreeBefore,20);
 return 1;
fail:
 if(added)Vbl_RemoveCall(marker);
 Rjp1_Stop();if(song)Rjp1_UnLoad(song);if(s)File_UnLoad(s);if(i)File_UnLoad(i);
 LanceMod_ShutdownPaula();if(mod)LanceMod_UnLoad(mod);return 0;
}
S16 GodLib_Game_Main(S16 argc,char **argv)
{(void)argc;(void)argv;GemDos_Super(0);Platform_Init();File_Init();Screen_Init(320,200,eGRAPHIC_COLOURMODE_4PLANE,0);gTestPass=run();gTestDone=1;while(!IKBD_GetKeyStatus(eIKBDSCAN_ESC))Screen_Update();Screen_DeInit();File_DeInit();Platform_DeInit();return !gTestPass;}
