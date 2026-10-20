/* Native VBL cadence/USP, one-shot/retrigger/loop and cross-mixer lifetime. */
#include <godlib/music/rjp1.h>
#include <godlib/music/lancemod.h>
#include <godlib/music/leonardmod.h>
#include <godlib/music/leonardmixer.h>
#include <godlib/music/paulamixer.h>
#include <godlib/file/file.h>
#include <godlib/memory/memory.h>
#include <godlib/platform/platform.h>
#include <godlib/screen/screen.h>
#include <godlib/system/system.h>
#include <godlib/gemdos/gemdos.h>
#include <godlib/ikbd/ikbd.h>
#include <godlib/vbl/vbl.h>
#include <string.h>
extern volatile U32 gRjp1Ticks;
extern void RjpMixerTest_Arm(void*,void*,U16,U16,U16);
extern void RjpCore_Stop(void),RjpLeo_Sync(void);
extern U8 *LeoSampleBuffer;
extern U16 blockSize,renderingBlock,emudmacon;
extern U32 pSampA[];
volatile U16 gMixerDone,gMixerPass,gMixerStage,gMixerCase;
volatile U32 gMixerTicks[8],gMixerVbls[8],gMixerSongBytes[8],gMixerWorkspace[8],gMixerFreeBefore,gMixerFreeAfter;
static void fixture(void){RjpLeo_Sync();LeonardMixer_Tick();}
#define CHECK(x,n) do{gMixerStage=n;if(!(x))goto fail;}while(0)
static U16 run(void)
{
 const char *names[2]={"JON","WARX4"};char a[16],b[16];
 sRjp1Song *song=0;sRjp1Info info;void *mod=0;U16 bank,mix,rate,mask,calls=Vbl_GetpVbl()->mCallCount,k=0,i,attached=0;U32 trap=*(U32*)0x80,usp,after,ticks,vbl;S8 pcm[32];
 gMixerFreeBefore=Memory_GetFree();
 for(bank=0;bank<2;++bank)for(mix=0;mix<2;++mix){
  strcpy(a,names[bank]);strcpy(b,names[bank]);strcat(a,".SNG");strcat(b,".INS");
  song=Rjp1_LoadEx(a,b,mix);CHECK(song,1);Rjp1_GetInfo(song,&info);CHECK(info.mMixer==mix,2);
  for(rate=1;rate<=2;++rate){gMixerCase=k;
   CHECK(Rjp1_Start(song,1,rate),3);
   gMixerSongBytes[k]=info.mResidentBytes;gMixerWorkspace[k]=Rjp1_GetAllocatedSize();
   CHECK(gMixerWorkspace[k]==Rjp1_GetWorkspaceSizeEx(rate,mix),4);
   CHECK(!LanceMod_Start(song,2)&&!LeonardMod_Start(song,2),5);
   CHECK(Rjp1_GetAllocatedSize()==gMixerWorkspace[k],6);
   ticks=gRjp1Ticks;vbl=Vbl_GetCounter();
   __asm__ volatile("move.l %%usp,%0":"=a"(usp));__asm__ volatile("move.l %0,%%usp"::"a"(0x12345678UL):"memory");
   while(gRjp1Ticks-ticks<128)__asm__ volatile("nop":::"memory");
   __asm__ volatile("move.l %%usp,%0":"=a"(after));__asm__ volatile("move.l %0,%%usp"::"a"(usp):"memory");
   gMixerTicks[k]=gRjp1Ticks-ticks;gMixerVbls[k]=Vbl_GetCounter()-vbl;
   CHECK(after==0x12345678UL && gMixerTicks[k]>=128 && gMixerTicks[k]+1>=gMixerVbls[k] && gMixerVbls[k]+1>=gMixerTicks[k],7);
   CHECK(Rjp1_SetSubSong(1),8);Rjp1_SetVolume(0);Vbl_WaitVbls(3);Rjp1_SetVolume(64);
   /* Actual Leonard one shot ends in silence, including nonzero last bytes. */
   if(mix){
    mask=System_GetIML();System_SetIML(7);Vbl_RemoveCall(Rjp1_Tick);RjpCore_Stop();
    for(i=0;i<32;++i)pcm[i]=(i&1)?120:-120;
    RjpMixerTest_Arm(PaulaMixer_Channels,pcm,4,1,0);
    *(U16*)(PaulaMixer_Channels+12)=64;*(U16*)(PaulaMixer_Channels+14)=200;
    CHECK(pSampA[0]==(U32)pcm&&pSampA[1]==(U32)pcm+8,9);
    attached=Vbl_AddCall(fixture);System_SetIML(mask);CHECK(attached,10);Vbl_WaitVbls(12);
    CHECK(!(emudmacon&1),11);
    {S16 off=renderingBlock-blockSize;if(off<0)off=3*blockSize;for(i=0;i<blockSize;++i)CHECK(!LeoSampleBuffer[off+i],12);}
    mask=System_GetIML();System_SetIML(7);Vbl_RemoveCall(fixture);attached=0;
    RjpMixerTest_Arm(PaulaMixer_Channels,pcm,4,2,2);pSampA[0]=(U32)pcm+6;
    RjpMixerTest_Arm(PaulaMixer_Channels,pcm,4,2,2);CHECK(pSampA[0]==(U32)pcm,13);
    attached=Vbl_AddCall(fixture);System_SetIML(mask);CHECK(attached,14);Vbl_WaitVbls(12);
    CHECK((emudmacon&1)&&pSampA[0]>=(U32)pcm+4&&pSampA[0]<(U32)pcm+8,15);
    mask=System_GetIML();System_SetIML(7);Vbl_RemoveCall(fixture);System_SetIML(mask);attached=0;
   }
   Rjp1_Stop();CHECK(!Rjp1_GetAllocatedSize()&&*(U32*)0x80==trap&&!(*(U8*)0xffff8901UL&3),16);++k;
  }
  CHECK(Rjp1_Start(song,1,2),17);Rjp1_UnLoad(song);song=0;CHECK(Vbl_GetpVbl()->mCallCount==calls,18);
 }
 /* Both MOD wrappers must still acquire/release the common native backends. */
 mod=LeonardMod_Load("LOSTPARO.MOD");CHECK(mod,19);
 CHECK(LeonardMod_Start(mod,1),20);Vbl_WaitVbls(10);CHECK(!PaulaMixer_Init(1,2),21);LeonardMod_ShutdownPaula();LeonardMod_UnLoad(mod);mod=0;
 mod=LanceMod_Load("LOSTPARO.MOD");CHECK(mod,22);CHECK(LanceMod_Start(mod,2),23);Vbl_WaitVbls(10);CHECK(!LeonardMixer_Init(1,2),24);LanceMod_ShutdownPaula();LanceMod_UnLoad(mod);mod=0;
 gMixerFreeAfter=Memory_GetFree();CHECK(gMixerFreeBefore==gMixerFreeAfter && *(U32*)0x80==trap && Vbl_GetpVbl()->mCallCount==calls,25);
 return 1;
fail:
 if(attached)Vbl_RemoveCall(fixture);
 Rjp1_Stop();if(song)Rjp1_UnLoad(song);LeonardMod_ShutdownPaula();LanceMod_ShutdownPaula();return 0;
}
S16 GodLib_Game_Main(S16 argc,char **argv)
{(void)argc;(void)argv;GemDos_Super(0);Platform_Init();File_Init();Screen_Init(320,200,eGRAPHIC_COLOURMODE_4PLANE,0);gMixerPass=run();gMixerDone=1;while(!IKBD_GetKeyStatus(eIKBDSCAN_ESC))Screen_Update();Screen_DeInit();File_DeInit();Platform_DeInit();return !gMixerPass;}
