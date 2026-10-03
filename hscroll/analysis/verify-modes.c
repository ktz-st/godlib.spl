#include <godlib/platform/platform.h>
#include <godlib/gemdos/gemdos.h>
#include <godlib/screen/screen.h>
#include <godlib/video/video.h>
volatile U16 gScreenModesResult=0xffff;
static U16 verify(void)
{
 U16 mode,i;
 for(mode=0;mode<4;++mode) {
  U16 w=mode&eSCREEN_SCROLL_H?352:320;
  U16 h=mode&eSCREEN_SCROLL_V?232:200;
  U16 x=w-320,y=h-200;
  Screen_Init(320,200,eGRAPHIC_COLOURMODE_4PLANE,mode);
  if(gScreenLogicGraphic.mWidth!=w || gScreenLogicGraphic.mHeight!=h
   || gScreenLogicGraphic.mpLineOffsets[1]!=w/2) return 10+mode;
  for(i=0;i<3;++i) if((U32)gScreenClass.mpBuffers[i]&255) return 20+mode;
  Screen_SetScrollX(65535);Screen_SetScrollY(y?65535:0);Screen_Update();
  if(Screen_GetScrollX()!=x || Screen_GetScrollY()!=y) return 30+mode;
  if((U32)Video_GetpPhysic()!=(U32)Screen_GetpPhysic()+(U32)y*(w/2)+(x>>4)*8)
   return 40+mode;
  if(*(volatile U8*)0xffff8265L || *(volatile U8*)0xffff820fL!=(w-320)/4)
   return 50+mode;
  Screen_DeInit();
 }
 {
  static const U16 cases[3][5]={{640,200,eSCREEN_SCROLL_H,640,200},
   {320,400,eSCREEN_SCROLL_V,320,432},{640,400,eSCREEN_SCROLL_H|eSCREEN_SCROLL_V,640,432}};
  for(mode=0;mode<3;++mode) {
   U16 w=cases[mode][3],h=cases[mode][4];
   Screen_Init(cases[mode][0],cases[mode][1],eGRAPHIC_COLOURMODE_4PLANE,cases[mode][2]);
   if(!gScreenClass.mpMemBase || gScreenLogicGraphic.mWidth!=w || gScreenLogicGraphic.mHeight!=h
    || Video_GetWidth()!=320 || Video_GetHeight()!=200) return 60+mode;
   Screen_SetScrollX(65535);Screen_SetScrollY(65535);Screen_Update();
   if(Screen_GetScrollX()!=w-320 || Screen_GetScrollY()!=h-200) return 70+mode;
   if((U32)Video_GetpPhysic()!=(U32)Screen_GetpPhysic()+(U32)(h-200)*(w/2)+((w-320)>>4)*8)
    return 80+mode;
   Screen_DeInit();
  }
 }
 Screen_Init(337,200,eGRAPHIC_COLOURMODE_4PLANE,eSCREEN_SCROLL_H);
 if(gScreenClass.mpMemBase) return 90;
 Screen_Init(1344,200,eGRAPHIC_COLOURMODE_4PLANE,eSCREEN_SCROLL_H);
 if(gScreenClass.mpMemBase) return 91;
 return 0;
}
S16 GodLib_Game_Main(S16 argc,char **argv)
{
 (void)argc;(void)argv;GemDos_Super(0);Platform_Init();
 gScreenModesResult=verify();
 for(;;) { /* retain result for debugger */ }
 return 0;
}
