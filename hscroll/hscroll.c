#include <godlib/chunky/chunky.h>
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
#include <string.h>
#define WIDTH 640
#ifdef HSCROLL_VERIFY_PATTERN
#define HEIGHT 232
static U16 sPattern[WIDTH*32UL/2];
static sGraphicCanvas sPatternCanvas;
static U16 sPalette[16]={0,0x777,0x700,0x070,0x007,0x770,0x707,0x077,
 0x333,0x555,0x733,0x373,0x337,0x773,0x737,0x555};
#else
#define HEIGHT 200
#endif
volatile U16 gHScrollReady,gSpriteStrideResult;
U16 gHScrollX,gHScrollY,gHScrollAuto=1;
extern U16 HScroll_VerifySprites(void);
#ifndef HSCROLL_VERIFY_PATTERN
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
 if(sBirdDrawn[page]) {
  rect.mX=sBirdSaved[page].mX;rect.mY=sBirdSaved[page].mY;
  rect.mWidth=16;rect.mHeight=16;
  Screen_Logic_Blit_Clip(&sBirdSaved[page],&rect,Screen_GetpBackGraphic());
  sBirdDrawn[page]=0;
 }
 if(!gBirdVisible) return;
 gBirdX=gHScrollX+(phase<288?phase:576-phase);
 phase=gBirdPhase%160;
 gBirdY=40+(phase<80?phase:160-phase);
 pos.mX=gBirdX;pos.mY=gBirdY;
 Screen_Logic_DrawSprite_Clip(&pos,sBird);
 sBirdSaved[page]=pos;sBirdDrawn[page]=1;
 if(gBirdMoving) ++gBirdPhase;
}
#endif

#ifdef HSCROLL_VERIFY_PATTERN
static U8 DrawBackground(void)
{
 U16 x,y; U8 *pixels=(U8*)sPattern;
 sGraphicRect rect={0,0,WIDTH,32};sGraphicPos pos={0,0};
 GraphicCanvas_Init(&sPatternCanvas,eGRAPHIC_COLOURMODE_8BPP,WIDTH,32);
 sPatternCanvas.mpVRAM=sPattern;
 for(y=0;y<32;++y) for(x=0;x<WIDTH;++x)
  pixels[(U32)y*WIDTH+x]=(x&15)==0 || (y&15)==0 ? 1 : 2+(((x>>4)+(y>>4))%14);
 for(y=0;y<HEIGHT;y+=32) {
  pos.mY=y;rect.mHeight=HEIGHT-y<32?HEIGHT-y:32;
  ChunkySurface_To4Plane(Screen_GetpBackGraphic(),&pos,&rect,&sPatternCanvas);
 }
 GraphicCanvas_DeInit(&sPatternCanvas);
 Video_SetPalST(sPalette);
 return 1;
}
#else
static U8 DrawBackground(void)
{
 U16 *picture;
 if(File_GetSize("PANORAMA.BIN")!=64032L) return 0;
 picture=File_Load("PANORAMA.BIN");
 if(!picture) return 0;
 Video_SetPalST(picture);
 Memory_Copy(64000UL,picture+16,Screen_GetpBack());
 File_UnLoad(picture);
 return 1;
}
#endif
static void CopyBackground(void)
{
 Memory_Copy((U32)(WIDTH/2)*HEIGHT,Screen_GetpBack(),Screen_GetpLogic());
 Memory_Copy((U32)(WIDTH/2)*HEIGHT,Screen_GetpBack(),Screen_GetpPhysic());
}
S16 GodLib_Game_Main(S16 argc,char **argv)
{
 S16 step=1;U8 quit=0;
 (void)argc;(void)argv;
 GemDos_Super(0);Platform_Init();File_Init();
 gSpriteStrideResult=HScroll_VerifySprites();
 if(gSpriteStrideResult || System_GetVDO()!=VDO_STE) {
  printf("STE required. Sprite stride test result: %u\n",(unsigned int)gSpriteStrideResult);
  GemDos_Cnecin();File_DeInit();Platform_DeInit();return 1;
 }
#ifdef HSCROLL_VERIFY_PATTERN
 Screen_Init(WIDTH,200,eGRAPHIC_COLOURMODE_4PLANE,eSCREEN_SCROLL_H|eSCREEN_SCROLL_V);
#else
 Screen_Init(WIDTH,HEIGHT,eGRAPHIC_COLOURMODE_4PLANE,eSCREEN_SCROLL_H);
#endif
 if(!gScreenClass.mpMemBase) { File_DeInit();Platform_DeInit();return 1; }
 if(!DrawBackground()) {
  printf("Cannot load PANORAMA.BIN (640x200).\n");GemDos_Cnecin();
  Screen_DeInit();File_DeInit();Platform_DeInit();return 1;
 }
 CopyBackground();
#ifndef HSCROLL_VERIFY_PATTERN
 if(!CreateBird()) { Screen_DeInit();File_DeInit();Platform_DeInit();return 1; }
#endif
 gHScrollReady=1;
 while(!quit) {
  IKBD_Update();
  while(IKBD_GetKbdBytesWaiting()) {
   U8 key=IKBD_PopKbdByte();
   if(key==eIKBDSCAN_ESC) quit=1;
   if(key==eIKBDSCAN_SPACE) gHScrollAuto^=1;
  }
  if(gHScrollAuto) {
   if(gHScrollX==320) step=-1;
   if(!gHScrollX) step=1;
   gHScrollX+=step;
  }
  else {
   if(IKBD_GetKeyStatus(eIKBDSCAN_LEFTARROW) && gHScrollX) --gHScrollX;
   if(IKBD_GetKeyStatus(eIKBDSCAN_RIGHTARROW) && gHScrollX<320) ++gHScrollX;
   if(IKBD_GetKeyStatus(eIKBDSCAN_UPARROW) && gHScrollY) --gHScrollY;
   if(IKBD_GetKeyStatus(eIKBDSCAN_DOWNARROW) && gHScrollY<HEIGHT-200) ++gHScrollY;
  }
  Screen_SetScrollX(gHScrollX);Screen_SetScrollY(gHScrollY);
#ifndef HSCROLL_VERIFY_PATTERN
  DrawBird();
#endif
  Screen_Update();
 }
#ifndef HSCROLL_VERIFY_PATTERN
 Sprite_Destroy(sBird);
#endif
 Screen_DeInit();File_DeInit();Platform_DeInit();return 0;
}
