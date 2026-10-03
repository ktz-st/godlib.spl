#include <godlib/memory/memory.h>
#include <godlib/file/file.h>
#include <godlib/gemdos/gemdos.h>
#include <godlib/ikbd/ikbd.h>
#include <godlib/platform/platform.h>
#include <godlib/screen/screen.h>
#include <godlib/video/video.h>
#include <godlib/system/system.h>
#include <godlib/sprite/sprite.h>
#include <godlib/graphic/graphic.h>
#include <stdio.h>
#define WIDTH 320
#define HEIGHT 400
volatile U16 gVScrollReady;
U16 gVScrollY=200,gVScrollAuto=1;
static sSprite *sBird;
static sGraphicPos sBirdSaved[2];
static U8 sBirdDrawn[2];
static U16 sBirdSource[80*16];
U16 gBirdVisible=1,gBirdMoving=1,gBirdPhase;
U16 gBirdX,gBirdY;
static U8 CreateBird(void)
{
 static const U16 silhouette[16]={0,0,0x8001,0xc003,0xe007,0x700e,0x381c,0x1c38,
  0x0ff0,0x07e0,0x03c0,0x0180,0,0,0,0};
 U16 y,p;U16 *mask;
 for(y=0;y<16;++y) for(p=0;p<4;++p) sBirdSource[y*80+p]=silhouette[y];
 mask=Sprite_MaskCreate(sBirdSource,16,16,4,4,0);
 if(!mask) return 0;
 sBird=Sprite_Create(sBirdSource,mask,16,16,4,4,0);
 Sprite_MaskDestroy(mask);
 return sBird!=0;
}
static void DrawBird(void)
{
 U16 page=Screen_GetLogicIndex(),phase=gBirdPhase%576;
 sGraphicRect rect; sGraphicPos pos;
 gBirdX=16+(phase<288?phase:576-phase);
 phase=gBirdPhase%160;
 gBirdY=gVScrollY+40+(phase<80?phase:160-phase);
 if(gBirdVisible && sBirdDrawn[page]
  && sBirdSaved[page].mX==gBirdX && sBirdSaved[page].mY==gBirdY) {
  if(gBirdMoving) ++gBirdPhase;
  return;
 }
 if(sBirdDrawn[page]) {
  rect.mX=sBirdSaved[page].mX;rect.mY=sBirdSaved[page].mY;
  rect.mWidth=16;rect.mHeight=16;
  Screen_Logic_Blit_Clip(&sBirdSaved[page],&rect,Screen_GetpBackGraphic());
  sBirdDrawn[page]=0;
 }
 if(!gBirdVisible) return;
 pos.mX=gBirdX;pos.mY=gBirdY;
 Screen_Logic_DrawSprite_Clip(&pos,sBird);
 sBirdSaved[page]=pos;sBirdDrawn[page]=1;
 if(gBirdMoving) ++gBirdPhase;
}
static U8 DrawBackground(void)
{
 U16 *picture;
 if(File_GetSize("TOWER.BIN")!=64032L) return 0;
 picture=File_Load("TOWER.BIN");
 if(!picture) return 0;
 Video_SetPalST(picture);
 Memory_Copy(64000UL,picture+16,Screen_GetpBack());
 File_UnLoad(picture);
 return 1;
}
static void CopyBackground(void)
{
 Memory_Copy((U32)(WIDTH/2)*gScreenBackGraphic.mHeight,Screen_GetpBack(),Screen_GetpLogic());
 Memory_Copy((U32)(WIDTH/2)*gScreenBackGraphic.mHeight,Screen_GetpBack(),Screen_GetpPhysic());
}
S16 GodLib_Game_Main(S16 argc,char **argv)
{
 S16 step=-1;U8 quit=0;
 (void)argc;(void)argv;
 GemDos_Super(0);Platform_Init();File_Init();
 if(System_GetVDO()!=VDO_STE) {
  printf("STE video hardware required.\n");GemDos_Cnecin();
  File_DeInit();Platform_DeInit();return 1;
 }
 Screen_Init(WIDTH,HEIGHT,eGRAPHIC_COLOURMODE_4PLANE,eSCREEN_SCROLL_V);
 if(!gScreenClass.mpMemBase) { File_DeInit();Platform_DeInit();return 1; }
 if(!DrawBackground()) {
  printf("Cannot load TOWER.BIN (320x400).\n");GemDos_Cnecin();
  Screen_DeInit();File_DeInit();Platform_DeInit();return 1;
 }
 CopyBackground();
 if(!CreateBird()) { Screen_DeInit();File_DeInit();Platform_DeInit();return 1; }
 gVScrollReady=1;
 while(!quit) {
  IKBD_Update();
  while(IKBD_GetKbdBytesWaiting()) {
   U8 key=IKBD_PopKbdByte();
   if(key==eIKBDSCAN_ESC) quit=1;
   if(key==eIKBDSCAN_SPACE) gVScrollAuto^=1;
  }
  if(gVScrollAuto) {
   if(gVScrollY==200) step=-1;
   if(!gVScrollY) step=1;
   gVScrollY+=step;
  }
  else {
   if(IKBD_GetKeyStatus(eIKBDSCAN_UPARROW) && gVScrollY) --gVScrollY;
   if(IKBD_GetKeyStatus(eIKBDSCAN_DOWNARROW) && gVScrollY<200) ++gVScrollY;
  }
  Screen_SetScrollY(gVScrollY);
  DrawBird();
  Screen_Update();
 }
 Sprite_Destroy(sBird);
 Screen_DeInit();File_DeInit();Platform_DeInit();return 0;
}
