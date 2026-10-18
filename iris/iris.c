/* SuperHex rotating hexagon shutter: dedicated fourth bitplane. */
#include "iris.h"
#include <godlib/gemdos/gemdos.h>
#include <godlib/font8x8/font8x8.h>
#include <godlib/ikbd/ikbd.h>
#include <godlib/memory/memory.h>
#include <godlib/platform/platform.h>
#include <godlib/screen/screen.h>
#include <godlib/system/system.h>
#include <godlib/vbl/vbl.h>
#include <godlib/video/video.h>
U16 gIrisStage,gIrisStep,gIrisPicture,gIrisAngle,gIrisPause,gIrisAuto;
U16 gIrisDrawStage,gIrisDrawStep,gIrisDrawPicture,gIrisDrawAngle,gIrisDrawH;
U16 gIrisUsingBlitter;
void *gIrisScreen;
volatile U16 gIrisReady,gIrisExited;
volatile U32 gIrisFrames,gIrisLastVbl,gIrisMissedVbl;
static U16 sPhase,sHold,sPages[2]={65535,65535};
static const U16 *sPalette=Iris_Palette;
static void LoadPicture(void)
{
 U16 i,ink=1;U32 best=0;
 sPalette=gIrisPicture?Iris_Palette2:Iris_Palette;
 Memory_Copy(32000,gIrisPicture?Iris_Image2:Iris_Image,Screen_GetpBack());
 for(i=1;i<7;++i){
  U16 c=sPalette[i];U32 light=0;U16 shift;
  for(shift=0;shift<12;shift+=4){U16 n=(c>>shift)&15;light+=((n&7)<<1)|(n>>3);}
  if(light>best){best=light;ink=i;}
 }
 Font8x8_PrintColourCanvas("SUPERHEX / ROTATING HEXAGON IRIS",Screen_GetpBackGraphic(),24,0,ink);
 Font8x8_PrintColourCanvas("N NEXT  A AUTO  P PAUSE  ESC EXIT",Screen_GetpBackGraphic(),24,192,ink);
 sPages[0]=sPages[1]=65535;
}
/* Clip before calling the fast, wholly visible GodLib ASM line path.
   Matches SuperHex's Cohen-Sutherland clipping; no off-screen pixel walks. */
static U16 Outcode(S32 x,S32 y)
{
 return (x<0?1:x>319?2:0)|(y<0?4:y>199?8:0);
}
static void Edge(S32 x0,S32 y0,S32 x1,S32 y1)
{
 U16 c0=Outcode(x0,y0),c1=Outcode(x1,y1);
 for(;;){
  U16 c;S32 x,y;
  if(!(c0|c1)){
   sGraphicBox line;
   line.mX0=(S16)x0;line.mX1=(S16)x1;line.mY0=(S16)y0;line.mY1=(S16)y1;
   GraphicCanvas_DrawLine_Clip(Screen_GetpLogicGraphic(),&line,15);return;
  }
  if(c0&c1)return;
  c=c0?c0:c1;
  if(c&8){x=x0+(x1-x0)*(199-y0)/(y1-y0);y=199;}
  else if(c&4){x=x0+(x1-x0)*(-y0)/(y1-y0);y=0;}
  else if(c&2){y=y0+(y1-y0)*(319-x0)/(x1-x0);x=319;}
  else{y=y0+(y1-y0)*(-x0)/(x1-x0);x=0;}
  if(c==c0){x0=x;y0=y;c0=Outcode(x0,y0);}
  else{x1=x;y1=y;c1=Outcode(x1,y1);}
 }
}
void Iris_Render(void) __attribute__((noinline));
void Iris_Render(void)
{
 U16 page=Screen_GetLogicIndex(),k;
 gIrisScreen=Screen_GetpLogic();
 gIrisDrawStage=gIrisStage;gIrisDrawStep=gIrisStep;gIrisDrawPicture=gIrisPicture;
 gIrisDrawAngle=gIrisAngle;gIrisDrawH=(U16)((U32)gIrisStep*220/40);
 if(gIrisStage || sPages[page]!=gIrisPicture){
  GraphicCanvas_CopyScreen(Screen_GetpLogicGraphic(),Screen_GetpBack());
  sPages[page]=gIrisStage?65535:gIrisPicture;
 }
 if(gIrisStage && gIrisDrawH>2){
  Iris_Fill(gIrisScreen,gIrisSpans);
  for(k=0;k<6;++k){
   Edge(gIrisX[k],gIrisY[k],gIrisX[k+1],gIrisY[k+1]);
  }
 }
}
void Iris_RenderEnd(void){}
void Iris_FrameDone(void) __attribute__((noinline));
void Iris_FrameDone(void){__asm__ volatile("" ::: "memory");}
static void Prepare(void)
{
 S16 a=(S16)sPhase+(gIrisStage==1?1:-1)*(S16)gIrisStep*14;
 while(a<0)a+=1536;
 while(a>=1536)a-=1536;
 gIrisAngle=(U16)a;
 Iris_Prepare((S16)((U32)gIrisStep*220/40),gIrisAngle);
}
S16 GodLib_Game_Main(S16 argc,char **argv)
{
 U16 quit=0;(void)argc;(void)argv;
 GemDos_Super(0);Platform_Init();
 Screen_Init(320,200,eGRAPHIC_COLOURMODE_4PLANE,0);
 if(!Screen_GetpMemBase()){Platform_DeInit();return 1;}
 gIrisUsingBlitter=System_GetBLT()==BLT_BLITTER;
 Graphic_SetBlitterEnable(gIrisUsingBlitter);
 LoadPicture();Memory_Clear(32000,Screen_GetpLogic());Memory_Clear(32000,Screen_GetpPhysic());
 gIrisReady=1;
 while(!quit){
  U32 now;Video_SetNextPalST(sPalette);Screen_Update();IKBD_Update();now=Vbl_GetCounter();
  if(gIrisFrames && now-gIrisLastVbl>1)gIrisMissedVbl+=now-gIrisLastVbl-1;
  gIrisLastVbl=now;
  while(IKBD_GetKbdBytesWaiting()){
   U8 key=IKBD_PopKbdByte();
   if(key==eIKBDSCAN_ESC)quit=1;
   if(key==eIKBDSCAN_P)gIrisPause^=1;
   if(key==eIKBDSCAN_A)gIrisAuto^=1;
   if(key==eIKBDSCAN_N && !gIrisStage){gIrisStage=1;gIrisStep=0;sHold=0;Prepare();}
  }
  Iris_Render();++gIrisFrames;Iris_FrameDone();
  if(!gIrisPause){
   sPhase+=2;if(sPhase>=1536)sPhase-=1536;
   if(gIrisStage==1){
    if(gIrisStep<40)++gIrisStep;
    else{gIrisPicture^=1;LoadPicture();gIrisStage=2;}
   }else if(gIrisStage==2){
    if(gIrisStep)--gIrisStep;else{gIrisStage=0;sHold=0;}
   }else if(gIrisAuto && ++sHold>=200){gIrisStage=1;gIrisStep=0;sHold=0;}
   if(gIrisStage)Prepare();
  }
 }
 Screen_DeInit();Platform_DeInit();gIrisExited=1;return 0;
}
