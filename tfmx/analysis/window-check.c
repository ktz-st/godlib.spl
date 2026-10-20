#include <godlib/music/tfmx.h>
#include <godlib/music/paulamixer.h>
#include <godlib/file/file.h>
#include <godlib/platform/platform.h>
#include <godlib/screen/screen.h>
#include <godlib/system/system.h>
#include <godlib/gemdos/gemdos.h>
#include <godlib/ikbd/ikbd.h>
#include <godlib/vbl/vbl.h>
extern U8 channela[],pSampA[];extern U16 emudmacon;
extern void TfmxCore_Tick(void),Tfmx_LancePrepare(void),Tfmx_LanceFinish(void);
volatile U16 gDone,gPass,gStage,gVoice,gOffset,gWant,gGot;
volatile U32 gSteps,gCountBad,gCountMaxDiff;
static U16 run(void){sTfmxSong *s=Tfmx_Load("SOUNDS.MDT","SOUNDS.SMP",0);U16 sr,t,i,j,period;U32 pos,end,loop,len,used,expected,diff;U8 *window,*v,*state,*regs;
 if(!s||!Tfmx_Start(s,0,2))return 0;
 sr=System_GetIML();System_SetIML(7);Vbl_RemoveCall(Tfmx_Tick);Tfmx_SetSubSong(0);System_SetIML(sr);
 for(t=0;t<4000;++t){TfmxCore_Tick();Tfmx_LancePrepare();
 for(i=0;i<4;++i){if(!(emudmacon&(1<<i)))continue;gVoice=i;v=PaulaMixer_Channels+20*i;state=pSampA+10*i;regs=channela+16*i;if(*(U16*)(v+12)>64){gStage=3;goto fail;}pos=*(U32*)state;end=*(U32*)(state+4);loop=*(U32*)regs;len=2UL**(U16*)(regs+4);window=*(U8**)v;
 for(j=0;j<672;++j){if(pos>=end){pos=loop;end=loop+len;}if(window[j]!=*(U8*)pos){gOffset=j;gWant=*(U8*)pos;gGot=window[j];gStage=1;goto fail;}++pos;}}
 PaulaMixer_Tick();
 for(i=0;i<4;++i){if(!(emudmacon&(1<<i)))continue;v=PaulaMixer_Channels+20*i;regs=channela+16*i;used=*(U32*)v-(*(U32*)(v+4)-672);period=*(U16*)(regs+6);if(!period)continue;expected=70938UL/period;diff=used>expected?used-expected:expected-used;if(diff>1)++gCountBad;if(diff>gCountMaxDiff)gCountMaxDiff=diff;}
 Tfmx_LanceFinish();++gSteps;}
 Tfmx_UnLoad(s);return 1;
fail:Tfmx_UnLoad(s);return 0;}
S16 GodLib_Game_Main(S16 a,char**b){(void)a;(void)b;GemDos_Super(0);Platform_Init();File_Init();Screen_Init(320,200,0,0);gPass=run();gDone=1;while(!IKBD_GetKeyStatus(eIKBDSCAN_ESC))Screen_Update();Screen_DeInit();File_DeInit();Platform_DeInit();return 0;}
