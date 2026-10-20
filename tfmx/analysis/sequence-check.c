#include <godlib/music/tfmx.h>
#include <godlib/file/file.h>
#include <godlib/platform/platform.h>
#include <godlib/screen/screen.h>
#include <godlib/system/system.h>
#include <godlib/gemdos/gemdos.h>
#include <godlib/ikbd/ikbd.h>
#include <godlib/vbl/vbl.h>
#include <string.h>
extern void TfmxRef_Init(void*,void*),TfmxRef_Start(U32),TfmxRef_Tick(void),TfmxCore_Tick(void);
extern U8 TfmxRefCustom[],emuDFF[],TfmxCore_State[];
volatile U16 gSequenceDone,gSequencePass,gSequenceSong,gSequenceField;
volatile U16 gPeriodMin[7]={65535,65535,65535,65535,65535,65535,65535},gPeriodMax[7];
volatile U32 gPeriodOutside[7];
volatile U16 gVolumeMax[7];
volatile U32 gVolumeOutside[7];
volatile U32 gSequenceSteps,gSequenceExpected,gSequenceActual;
static U16 run(void)
{
 sTfmxSong *s=0;void *mdat=0,*smpl=0;U16 song,i,field,sr,tick,ok=0;U32 x,y,bank;U8 *a,*b;
 mdat=File_Load("SOUNDS.MDT");smpl=File_Load("SOUNDS.SMP");s=Tfmx_Load("SOUNDS.MDT","SOUNDS.SMP",1);if(!s || !mdat || !smpl)goto done;
 if(!Tfmx_Start(s,0,2))goto done;
 sr=System_GetIML();System_SetIML(7);Vbl_RemoveCall(Tfmx_Tick);System_SetIML(sr);
 TfmxRef_Init(mdat,smpl);
 for(song=0;song<7;++song){gSequenceSong=song;Tfmx_SetSubSong(song);memset(TfmxRefCustom+0xa0,0,64);TfmxRef_Init(mdat,smpl);TfmxRef_Start(song);bank=*(U32*)(TfmxCore_State+4);
  for(tick=0;tick<4000;++tick){TfmxCore_Tick();TfmxRef_Tick();
   for(i=0;i<4;++i){a=emuDFF+0xa0+16*i;b=TfmxRefCustom+0xa0+16*i;
    if(*(U16*)(a+8)>gVolumeMax[song])gVolumeMax[song]=*(U16*)(a+8);
    if(*(U16*)(a+8)>64)++gVolumeOutside[song];
    if(*(U16*)(a+8)){U16 per=*(U16*)(a+6);if(per<gPeriodMin[song])gPeriodMin[song]=per;if(per>gPeriodMax[song])gPeriodMax[song]=per;if(per<108 || per>907)++gPeriodOutside[song];}
    for(field=0;field<4;++field){gSequenceField=4*i+field;
     if(!field){x=*(U32*)a;y=*(U32*)b;if(x)x-=bank;if(y)y-=(U32)smpl;}
     else{x=*(U16*)(a+2+2*field);y=*(U16*)(b+2+2*field);}
     if(x!=y){gSequenceActual=x;gSequenceExpected=y;goto done;}
    }
   }
   ++gSequenceSteps;
  }
 }
 ok=1;
done:if(s)Tfmx_UnLoad(s);if(mdat){File_UnLoad(mdat);}if(smpl){File_UnLoad(smpl);}return ok;
}
S16 GodLib_Game_Main(S16 argc,char **argv)
{(void)argc;(void)argv;GemDos_Super(0);Platform_Init();File_Init();Screen_Init(320,200,eGRAPHIC_COLOURMODE_4PLANE,0);gSequencePass=run();gSequenceDone=1;while(!IKBD_GetKeyStatus(eIKBDSCAN_ESC))Screen_Update();Screen_DeInit();File_DeInit();Platform_DeInit();return !gSequencePass;}
