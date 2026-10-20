/* Native VectorDean RJP1 music, scheduled by GodLib at PAL VBL. */
#include <godlib/music/rjp1.h>
#include <godlib/font8x8/font8x8.h>
#include <godlib/file/file.h>
#include <godlib/gemdos/gemdos.h>
#include <godlib/ikbd/ikbd.h>
#include <godlib/platform/platform.h>
#include <godlib/screen/screen.h>
#include <godlib/system/system.h>
#include <godlib/video/video.h>
#include <stdio.h>
volatile U16 gRjpReady,gRjpExited,gRjpRate=2,gRjpSong=1,gRjpBank,gRjpRaster,gRjpMixer;
volatile U32 gRjpFrames;
volatile U16 gRjpExitReason;
static const char *names[2]={"JON","WARX4"};
static sRjp1Song *song;
static sRjp1Info info;
static void scene(void)
{
 char line[41];U16 i; sGraphicCanvas *c=Screen_GetpBackGraphic();
 GraphicCanvas_ClearScreen(c);
 Font8x8_PrintColourCanvas(gRjpMixer?"RJP1 / LEONARD PAULA":"RJP1 / LANCE PAULA",c,72,8,1);
 sprintf(line,"%s / SONG %u OF %u",names[gRjpBank],gRjpSong,info.mSubSongs-1);
 Font8x8_PrintColourCanvas(line,c,40,28,1);
 sprintf(line,"RATE %s KHZ  RAM %lu+%lu",gRjpRate==1?"12.5":gRjpRate==2?"25":"50",info.mResidentBytes,Rjp1_GetAllocatedSize());
 Font8x8_PrintColourCanvas(line,c,8,48,1);
 for(i=0;i<4;++i){sprintf(line,"CH%u",i+1);Font8x8_PrintColourCanvas(line,c,(S16)(40+i*64),72,(S16)(i+2));}
 Font8x8_PrintColourCanvas("1/2/3 RATE  B MIX  N SONG  M MUSIC",c,24,176,1);
 Font8x8_PrintColourCanvas("F1 CPU  ESC EXIT",c,96,192,1);
 GraphicCanvas_CopyScreen(Screen_GetpLogicGraphic(),Screen_GetpBack());
 GraphicCanvas_CopyScreen(Screen_GetpPhysicGraphic(),Screen_GetpBack());
}
static U8 load(void)
{
 char a[16],b[16];
 Rjp1_UnLoad(song);song=0;
 sprintf(a,"%s.SNG",names[gRjpBank]);sprintf(b,"%s.INS",names[gRjpBank]);
 song=Rjp1_LoadEx(a,b,gRjpMixer);if(!song)return 0;
 Rjp1_GetInfo(song,&info);gRjpSong=1;
 return Rjp1_Start(song,gRjpSong,(U8)gRjpRate);
}
S16 GodLib_Game_Main(S16 argc,char **argv)
{
 static U16 pal[16]={0,0x777,0x740,0x074,0x047,0x707};U16 vol[4],i,changed,quit=0;
 (void)argc;(void)argv;GemDos_Super(0);Platform_Init();File_Init();
 if(System_GetMCH()!=MCH_STE && System_GetMCH()!=MCH_MEGASTE){GemDos_Cconws("RJP1 requires STE DMA sound.\r\n");goto done;}
 Screen_Init(320,200,eGRAPHIC_COLOURMODE_4PLANE,0);Video_SetPalST(pal);
 if(!load()){gRjpExitReason=2;goto screenDone;}
 scene();gRjpReady=1;
 while(!quit){
  Screen_Update();IKBD_Update();changed=0;
  while(IKBD_GetKbdBytesWaiting()){
   U8 key=IKBD_PopKbdByte();
   if(key==eIKBDSCAN_ESC || key==eIKBDSCAN_SPACE)quit=1;
   if(key>=eIKBDSCAN_1 && key<=eIKBDSCAN_3){
    gRjpRate=key-eIKBDSCAN_1+1;
    if(gRjpMixer && gRjpRate==3)gRjpRate=2;
    if(!Rjp1_Start(song,gRjpSong,(U8)gRjpRate)){gRjpExitReason=3;goto screenDone;}
    changed=1;
   }
   if(key==eIKBDSCAN_B){gRjpMixer^=1;if(gRjpMixer && gRjpRate==3)gRjpRate=2;if(!load()){gRjpExitReason=2;goto screenDone;}changed=1;}
   if(key==eIKBDSCAN_N){gRjpSong=(gRjpSong+1)%info.mSubSongs;Rjp1_SetSubSong(gRjpSong);changed=1;}
   if(key==eIKBDSCAN_M){gRjpBank^=1;if(!load()){gRjpExitReason=2;goto screenDone;}changed=1;}
   if(key==eIKBDSCAN_F1){gRjpRaster^=1;Rjp1_SetRasterDebug((U8)gRjpRaster);}
  }
  if(changed)scene();
  Rjp1_GetVolumes(vol);
  for(i=0;i<4;++i){sGraphicRect rect={(S16)(40+i*64),88,32,72};GraphicCanvas_DrawBox(Screen_GetpLogicGraphic(),&rect,0);rect.mY=(S16)(160-vol[i]);rect.mHeight=(S16)vol[i];if(vol[i])GraphicCanvas_DrawBox(Screen_GetpLogicGraphic(),&rect,(S16)(i+2));}
  ++gRjpFrames;
 }
if(!gRjpExitReason)gRjpExitReason=1;
screenDone:
 Rjp1_UnLoad(song);song=0;gRjpExited=1;Screen_DeInit();
done: File_DeInit();Platform_DeInit();return 0;
}
