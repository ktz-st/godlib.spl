/* UGH! four-channel TFMX, automatic PAL VBL with selectable Paula mixer. */
#include <godlib/music/tfmx.h>
#include <godlib/font8x8/font8x8.h>
#include <godlib/file/file.h>
#include <godlib/gemdos/gemdos.h>
#include <godlib/ikbd/ikbd.h>
#include <godlib/platform/platform.h>
#include <godlib/screen/screen.h>
#include <godlib/system/system.h>
#include <godlib/video/video.h>
#include <stdio.h>
volatile U16 gTfmxReady,gTfmxExited,gTfmxRate=2,gTfmxSong=0,gTfmxBank,gTfmxRaster,gTfmxMixer;
volatile U32 gTfmxFrames;
volatile U16 gTfmxExitReason;

static sTfmxSong *song;
static sTfmxInfo info;
static void scene(void)
{
 char line[41];U16 i; sGraphicCanvas *c=Screen_GetpBackGraphic();
 GraphicCanvas_ClearScreen(c);
 Font8x8_PrintColourCanvas(gTfmxMixer?"TFMX / LEONARD PAULA":"TFMX / LANCE PAULA",c,72,8,1);
 sprintf(line,"%s / SONG %u OF %u","UGH!",gTfmxSong,info.mSubSongs-1);
 Font8x8_PrintColourCanvas(line,c,40,28,1);
 sprintf(line,"RATE %s KHZ  RAM %lu+%lu",gTfmxRate==1?"12.5":gTfmxRate==2?"25":"50",info.mResidentBytes,Tfmx_GetAllocatedSize());
 Font8x8_PrintColourCanvas(line,c,8,48,1);
 for(i=0;i<4;++i){sprintf(line,"CH%u",i+1);Font8x8_PrintColourCanvas(line,c,(S16)(40+i*64),72,(S16)(i+2));}
 Font8x8_PrintColourCanvas("1/2 RATE  B MIX  N SONG",c,64,176,1);
 Font8x8_PrintColourCanvas("F1 CPU  ESC EXIT",c,96,192,1);
 GraphicCanvas_CopyScreen(Screen_GetpLogicGraphic(),Screen_GetpBack());
 GraphicCanvas_CopyScreen(Screen_GetpPhysicGraphic(),Screen_GetpBack());
}
static U8 load(void)
{
 Tfmx_UnLoad(song);song=0;
 song=Tfmx_Load("SOUNDS.MDT","SOUNDS.SMP",gTfmxMixer);if(!song)return 0;
 Tfmx_GetInfo(song,&info);gTfmxSong=0;
 return Tfmx_Start(song,gTfmxSong,(U8)gTfmxRate);
}
S16 GodLib_Game_Main(S16 argc,char **argv)
{
 static U16 pal[16]={0,0x777,0x740,0x074,0x047,0x707};U16 vol[4],i,changed,quit=0;
 (void)argc;(void)argv;GemDos_Super(0);Platform_Init();File_Init();
 if(System_GetMCH()!=MCH_STE && System_GetMCH()!=MCH_MEGASTE){GemDos_Cconws("TFMX requires STE DMA sound.\r\n");goto done;}
 Screen_Init(320,200,eGRAPHIC_COLOURMODE_4PLANE,0);Video_SetPalST(pal);
 if(!load()){gTfmxExitReason=2;goto screenDone;}
 scene();gTfmxReady=1;
 while(!quit){
  Screen_Update();IKBD_Update();changed=0;
  while(IKBD_GetKbdBytesWaiting()){
   U8 key=IKBD_PopKbdByte();
   if(key==eIKBDSCAN_ESC || key==eIKBDSCAN_SPACE)quit=1;
   if(key>=eIKBDSCAN_1 && key<=eIKBDSCAN_2){
    gTfmxRate=key-eIKBDSCAN_1+1;
    if(gTfmxMixer && gTfmxRate==3)gTfmxRate=2;
    if(!Tfmx_Start(song,gTfmxSong,(U8)gTfmxRate)){gTfmxExitReason=3;goto screenDone;}
    changed=1;
   }
   if(key==eIKBDSCAN_B){gTfmxMixer^=1;if(gTfmxMixer && gTfmxRate==3)gTfmxRate=2;if(!load()){gTfmxExitReason=2;goto screenDone;}changed=1;}
   if(key==eIKBDSCAN_N){gTfmxSong=(gTfmxSong+1)%info.mSubSongs;Tfmx_SetSubSong(gTfmxSong);changed=1;}
   if(key==eIKBDSCAN_F1){gTfmxRaster^=1;Tfmx_SetRasterDebug((U8)gTfmxRaster);}
  }
  if(changed)scene();
  Tfmx_GetVolumes(vol);
  for(i=0;i<4;++i){sGraphicRect rect={(S16)(40+i*64),88,32,72};GraphicCanvas_DrawBox(Screen_GetpLogicGraphic(),&rect,0);rect.mY=(S16)(160-vol[i]);rect.mHeight=(S16)vol[i];if(vol[i])GraphicCanvas_DrawBox(Screen_GetpLogicGraphic(),&rect,(S16)(i+2));}
  ++gTfmxFrames;
 }
if(!gTfmxExitReason)gTfmxExitReason=1;
screenDone:
 Tfmx_UnLoad(song);song=0;gTfmxExited=1;Screen_DeInit();
done: File_DeInit();Platform_DeInit();return 0;
}
