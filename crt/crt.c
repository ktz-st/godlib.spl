/* Three image planes plus a CRT brightness mask. Raster work is 68000 ASM. */
#include "crt.h"
#include <godlib/gemdos/gemdos.h>
#include <godlib/font8x8/font8x8.h>
#include <godlib/ikbd/ikbd.h>
#include <godlib/memory/memory.h>
#include <godlib/platform/platform.h>
#include <godlib/screen/screen.h>
#include <godlib/system/system.h>
#include <godlib/video/video.h>
#include <godlib/vbl/vbl.h>
S16 gCrtX[11],gCrtY,gCrtBand;
U16 gCrtScan=1;
U8 *gCrtScreen;sCrtHistory *gCrtHistory;
const U8 *gCrtSource=Crt_Source,*gCrtTvSource;
const U16 *gCrtNextPalette;
U16 gCrtTvDrawMode,gCrtTvDrawStep,gCrtTvDrawPicture;
U16 gCrtTvStep,gCrtTvMode=1,gCrtPicture,gCrtTvTick;
U16 gCrtTvHeights[2],*gCrtTvPageHeight;
S16 gCrtTvRowCache[2][200],*gCrtTvRows;
sCrtHistory gCrtOld[2];
volatile U16 gCrtReady,gCrtExited,gCrtAuto=1,gCrtForce,gCrtPause,gCrtLight=1,gCrtBurst;
volatile U32 gCrtFrames,gCrtMissedVbl,gCrtLastVbl;
static U16 sCrtRand=0x4a31,sWait=120,sJitter,sJitterWait=45,sPhase;
static S16 sJitterX;
static U16 CrtRand(void){sCrtRand=(U16)((U32)sCrtRand*25173UL+13849UL);return sCrtRand;}
void Crt_Update(void) __attribute__((noinline));
void Crt_Update(void)
{
 U16 i;S16 x=0;
 if(gCrtPause)return;
 sPhase+=3;if(sPhase>=220)sPhase-=220;gCrtBand=gCrtLight?(S16)sPhase-22:-32;
 if(gCrtAuto && !gCrtForce && !gCrtBurst){if(sWait)--sWait;else{gCrtBurst=8+(CrtRand()&3);sWait=200+(CrtRand()&255);}}
 if(sJitter)--sJitter;
 else if(sJitterWait)--sJitterWait;
 else{sJitter=2+(CrtRand()&1);sJitterX=(CrtRand()&1)?1:-1;sJitterWait=40+(CrtRand()&63);}
 if(gCrtAuto && sJitter)x=sJitterX;
 gCrtY=0;
 if(gCrtForce || gCrtBurst){
  gCrtY=(S16)(CrtRand()&3)-1;
  for(i=0;i<11;++i){U16 r=CrtRand();gCrtX[i]=(r&0x100)?(S16)((r>>4)&15)-7:x;}
 }else for(i=0;i<11;++i)gCrtX[i]=x;
 if(gCrtBurst)--gCrtBurst;
}
void Crt_UpdateEnd(void){}
void Crt_FrameDone(void) __attribute__((noinline));
void Crt_FrameDone(void){__asm__ volatile("" ::: "memory");}
static void Crt_Invalidate(U16 height)
{
 U16 p,y;
 for(p=0;p<2;++p){
  gCrtTvHeights[p]=height;
  for(y=0;y<200;++y)gCrtTvRowCache[p][y]=-1;
  for(y=0;y<11;++y)gCrtOld[p].x[y]=32767;
  gCrtOld[p].y=32767;gCrtOld[p].band=-32;gCrtOld[p].scan=gCrtScan^1;
 }
}
static void Crt_LoadPicture(void)
{
 sGraphicCanvas *canvas;
 Memory_Copy(32000,gCrtPicture?Crt_Image2:Crt_Image,Screen_GetpBack());
 gCrtSource=gCrtPicture?Crt_Source2:Crt_Source;
 canvas=Screen_GetpBackGraphic();
 Font8x8_PrintColourCanvas("CRT / WASTELAND RELAY",canvas,80,0,7);
 Font8x8_PrintColourCanvas("A AUTO  S SCANLINES  B BRIGHT BAND",canvas,32,8,7);
 Font8x8_PrintColourCanvas("N NEXT G GLITCH SPACE BURST P PAUSE ESC",canvas,0,192,7);
 gCrtTvSource=(const U8*)Screen_GetpBack();
 gCrtNextPalette=gCrtPicture?Crt_Palette2:Crt_Palette;
 Video_SetPalST(gCrtNextPalette);
}
void Crt_TvUpdate(void) __attribute__((noinline));
void Crt_TvUpdate(void)
{
 /* Both display pages get the exact endpoint; palettes switch only after
    black has been displayed. P freezes interference, not the power sequence. */
 gCrtNextPalette=(gCrtPicture?Crt_TvPalettes2:Crt_TvPalettes)+(gCrtTvStep<<4);
 if(++gCrtTvTick<2)return;
 gCrtTvTick=0;
 if(gCrtTvMode==1){
  if(gCrtTvStep+1<Crt_TvCount)++gCrtTvStep;
  else{gCrtTvMode=0;Crt_Invalidate(200);}
 }else if(gCrtTvMode==2){
  if(gCrtTvStep)--gCrtTvStep;
  else{gCrtTvMode=3;gCrtTvTick=0;}
 }else if(gCrtTvMode==3){
  gCrtPicture^=1;Crt_LoadPicture();Crt_Invalidate(0);
  gCrtTvMode=1;gCrtTvStep=0;
 }
}
void Crt_TvUpdateEnd(void){}
S16 GodLib_Game_Main(S16 argc,char **argv)
{
 U16 quit=0,p;(void)argc;(void)argv;
 GemDos_Super(0);Platform_Init();
 if(!System_GetBLT()){GemDos_Cconws("CRT requires an Atari BLiTTER (STE/Mega ST).\r\n");Platform_DeInit();gCrtExited=1;return 1;}
 Screen_Init(320,200,eGRAPHIC_COLOURMODE_4PLANE,0);
 if(!gScreenClass.mpMemBase){Platform_DeInit();gCrtExited=1;return 1;}
 Crt_LoadPicture();Crt_Invalidate(0);
 Memory_Clear(32000,Screen_GetpLogic());Memory_Clear(32000,Screen_GetpPhysic());
 gCrtReady=1;
 while(!quit){
  U32 now;Video_SetNextPalST(gCrtNextPalette);Screen_Update();IKBD_Update();now=Vbl_GetCounter();
  if(gCrtFrames && now-gCrtLastVbl>1)gCrtMissedVbl+=now-gCrtLastVbl-1;
  gCrtLastVbl=now;
  while(IKBD_GetKbdBytesWaiting()){
   U8 k=IKBD_PopKbdByte();
   if(k==eIKBDSCAN_ESC)quit=1;
   if(k==eIKBDSCAN_N && !gCrtTvMode){
    gCrtTvMode=2;gCrtTvStep=Crt_TvCount-1;gCrtTvTick=0;Crt_Invalidate(200);
   }
   if(k==eIKBDSCAN_SPACE)gCrtBurst=10;
   if(k==eIKBDSCAN_G)gCrtForce^=1;
   if(k==eIKBDSCAN_A)gCrtAuto^=1;
   if(k==eIKBDSCAN_P)gCrtPause^=1;
   if(k==eIKBDSCAN_S)gCrtScan^=1;
   if(k==eIKBDSCAN_B)gCrtLight^=1;
  }
  p=Screen_GetLogicIndex();gCrtScreen=(U8*)Screen_GetpLogic();gCrtHistory=&gCrtOld[p];
  gCrtTvDrawMode=gCrtTvMode;gCrtTvDrawStep=gCrtTvStep;gCrtTvDrawPicture=gCrtPicture;
  if(gCrtTvMode){
   gCrtTvPageHeight=&gCrtTvHeights[p];gCrtTvRows=gCrtTvRowCache[p];
   Crt_TvRender();Crt_TvUpdate();
  }else{Crt_Update();Crt_Render();}
  ++gCrtFrames;Crt_FrameDone();
 }
 Screen_DeInit();Platform_DeInit();gCrtExited=1;return 0;
}
