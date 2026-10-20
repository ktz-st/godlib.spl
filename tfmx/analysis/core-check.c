#include <godlib/music/tfmx.h>
#include <godlib/music/paulamixer.h>
#include <godlib/music/leonardmixer.h>
#include <godlib/music/rjp1.h>
#include <godlib/file/file.h>
#include <godlib/memory/memory.h>
#include <godlib/platform/platform.h>
#include <godlib/screen/screen.h>
#include <godlib/system/system.h>
#include <godlib/gemdos/gemdos.h>
#include <godlib/ikbd/ikbd.h>
#include <godlib/vbl/vbl.h>
extern volatile U32 gTfmxTicks,gTfmxFaults;
extern U8 channela[64],pSampA[40],emuDFF[];
extern U16 emudmacon;
extern void TfmxDmaWrite(void),Tfmx_LancePrepare(void),Tfmx_LanceFinish(void);
volatile U16 gTestDone,gTestPass,gTestStage,gTestCase;
volatile U32 gTestTicks[4],gTestVbls[4],gTestSongBytes[4],gTestWorkspace[4],gTestFreeBefore,gTestFreeAfter;
#define CHECK(x,n) do{gTestStage=n;if(!(x))goto fail;}while(0)
static U16 run(void)
{
 sTfmxSong *s=0;sTfmxInfo info;U16 mix,rate,k=0,sr,i,j,calls=Vbl_GetpVbl()->mCallCount;U32 trap=*(U32*)0x80,ticks,vbl,usp,after,pos,end,loop,len,expected,consumed;U8 *window,*raw;
 gTestFreeBefore=Memory_GetFree();
 for(mix=0;mix<2;++mix){
  s=Tfmx_Load("SOUNDS.MDT","SOUNDS.SMP",mix);CHECK(s && Tfmx_GetInfo(s,&info) && info.mSubSongs==7 && info.mMixer==mix,1);
  for(rate=1;rate<=2;++rate){gTestCase=k;CHECK(Tfmx_Start(s,0,rate),2);
   gTestSongBytes[k]=info.mResidentBytes;gTestWorkspace[k]=Tfmx_GetAllocatedSize();
   CHECK(!PaulaMixer_Init(1,2)&&!LeonardMixer_Init(1,2),3);
   sr=System_GetIML();System_SetIML(7);ticks=gTfmxTicks;vbl=Vbl_GetCounter();
   __asm__ volatile("move.l %%usp,%0":"=a"(usp));__asm__ volatile("move.l %0,%%usp"::"a"(0x12345678UL):"memory");System_SetIML(sr);
   while(gTfmxTicks-ticks<128)__asm__ volatile("nop":::"memory");
   sr=System_GetIML();System_SetIML(7);__asm__ volatile("move.l %%usp,%0":"=a"(after));__asm__ volatile("move.l %0,%%usp"::"a"(usp):"memory");
   gTestTicks[k]=gTfmxTicks-ticks;gTestVbls[k]=Vbl_GetCounter()-vbl;System_SetIML(sr);
   CHECK(after==0x12345678UL && gTestTicks[k]>=128 && (mix ? gTestTicks[k]<=gTestVbls[k] : gTestTicks[k]==gTestVbls[k]) && !gTfmxFaults,4);
   /* Original engine may write DMA clear/set repeatedly at an identical LC.
      Verify immediate latching, phase reset and a real reload window. */
   sr=System_GetIML();System_SetIML(7);Vbl_RemoveCall(Tfmx_Tick);
   raw=*(U8**)channela;CHECK(raw && *(U16*)(channela+4),5);
   *(U16*)(emuDFF+0x96)=1;TfmxDmaWrite();CHECK(!(emudmacon&1),6);
   *(U16*)(channela+4)=4;*(U16*)(channela+6)=200;*(U16*)(channela+8)=64;
   *(U16*)(emuDFF+0x96)=0x8001;TfmxDmaWrite();CHECK(*(U8**)pSampA==raw && *(U32*)(pSampA+4)==(U32)raw+8,7);
   *(U32*)pSampA=(U32)raw+6;*(U16*)(pSampA+8)=123;
   TfmxDmaWrite();CHECK(*(U8**)pSampA==raw && !*(U16*)(pSampA+8),8);
   if(!mix){
    *(U32*)pSampA=(U32)raw+6;*(U8**)channela=raw+2;*(U16*)(channela+4)=2;
    pos=(U32)raw+6;end=(U32)raw+8;loop=(U32)raw+2;len=4;
    /* TFMX envelopes routinely produce 65. Native Lance only accepts 0..64:
       65 aliases its ratio-table denominator to 1 and can mute its partner. */
    *(U16*)(channela+8)=65;
    Tfmx_LancePrepare();CHECK(*(U16*)(PaulaMixer_Channels+12)==64,18);
    window=*(U8**)PaulaMixer_Channels;CHECK(window,9);expected=pos;
    for(i=0;i<672;++i){if(expected>=end){expected=loop;end=loop+len;}CHECK((S8)window[i]==(S8)*(U8*)expected,10);++expected;}
    PaulaMixer_Tick();consumed=*(U32*)PaulaMixer_Channels-(U32)window;CHECK(consumed<672,11);
    Tfmx_LanceFinish();expected=(U32)raw+6+consumed;if(expected>=(U32)raw+8)expected=loop+(expected-(U32)raw-8)%len;
    CHECK(*(U32*)pSampA==expected && !gTfmxFaults,12);
   }
   System_SetIML(sr);
   for(j=0;j<7;++j){CHECK(Tfmx_Start(s,j,rate),13);Vbl_WaitVbls(128);CHECK(!gTfmxFaults,14);}
   Tfmx_Stop();CHECK(!Tfmx_GetAllocatedSize() && Vbl_GetpVbl()->mCallCount==calls && *(U32*)0x80==trap && !(*(U8*)0xffff8901UL&3),15);++k;
  }
  CHECK(Tfmx_Start(s,0,2),16);Tfmx_UnLoad(s);s=0;
 }
 gTestFreeAfter=Memory_GetFree();CHECK(gTestFreeBefore==gTestFreeAfter && Vbl_GetpVbl()->mCallCount==calls,17);return 1;
fail:
 System_SetIML(3);Tfmx_Stop();if(s)Tfmx_UnLoad(s);return 0;
}
S16 GodLib_Game_Main(S16 argc,char **argv)
{(void)argc;(void)argv;GemDos_Super(0);Platform_Init();File_Init();Screen_Init(320,200,eGRAPHIC_COLOURMODE_4PLANE,0);gTestPass=run();gTestDone=1;while(!IKBD_GetKeyStatus(eIKBDSCAN_ESC))Screen_Update();Screen_DeInit();File_DeInit();Platform_DeInit();return !gTestPass;}
