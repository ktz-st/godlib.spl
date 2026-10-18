/* Six rotating light/dark wedges from SuperHex. Example only, no library changes. */
#include <godlib/base/base.h>
#include <godlib/gemdos/gemdos.h>
#include <godlib/font8x8/font8x8.h>
#include <godlib/ikbd/ikbd.h>
#include <godlib/memory/memory.h>
#include <godlib/platform/platform.h>
#include <godlib/screen/screen.h>
#include <godlib/system/system.h>
#include <godlib/vbl/vbl.h>
#include <godlib/video/video.h>
#ifndef WEDGES_REALTIME
extern U8 *gWedgesCache;
U16 Wedges_BuildFrames(void);
void Wedges_Copy(const void *source,void *dest,U16 inverse);
#else
void Wedges_Live(void *dest,U16 *history,U16 phase,U16 inverse);
U16 gWedgesHistory[2][1202]; /* inverse, phase, 200 rows x 3 mask/offset longs */
#endif
U16 gWedgesAngle,gWedgesSpeed=6,gWedgesPause,gWedgesBlitter,gWedgesHasBlitter;
S16 gWedgesDirection=1;
U16 gWedgesDrawAngle,gWedgesDrawFrame,gWedgesDrawInverse,gWedgesCopied;
void *gWedgesScreen;
volatile U16 gWedgesReady,gWedgesExited;
#ifdef WEDGES_REALTIME
volatile U16 gWedgesLate[32]; /* diagnostic counters for missed phases */
#endif
volatile U32 gWedgesFrames,gWedgesLastVbl,gWedgesMissedVbl;
static U16 sPageFrame[2]={65535,65535};
static const U16 sPalette[16]={
 0x013,0x013,0xfff,0xfff,0x8ac,0x8ac,0xfff,0xfff,
 0x013,0x013,0xfff,0xfff,0x8ac,0x8ac,0xfff,0xfff
};
void Wedges_Render(void) __attribute__((noinline));
void Wedges_Render(void)
{
 U16 page=Screen_GetLogicIndex(),key;
 gWedgesDrawAngle=gWedgesAngle;
 gWedgesDrawFrame=(gWedgesAngle&255)>>3;
 gWedgesDrawInverse=(gWedgesAngle>>8)&1;
 key=gWedgesDrawFrame|(gWedgesDrawInverse<<5);
 gWedgesScreen=Screen_GetpLogic();gWedgesCopied=0;
 if(sPageFrame[page]!=key){
#ifdef WEDGES_REALTIME
  Wedges_Live(gWedgesScreen,gWedgesHistory[page],gWedgesDrawFrame,gWedgesDrawInverse);
#else
  Wedges_Copy(gWedgesCache+(U32)gWedgesDrawFrame*8000UL,gWedgesScreen,gWedgesDrawInverse);
#endif
  sPageFrame[page]=key;gWedgesCopied=1;
 }
}
void Wedges_RenderEnd(void){}
void Wedges_FrameDone(void) __attribute__((noinline));
void Wedges_FrameDone(void){__asm__ volatile("" ::: "memory");}
S16 GodLib_Game_Main(S16 argc,char **argv)
{
 U16 quit=0;S16 next;(void)argc;(void)argv;
 GemDos_Super(0);Platform_Init();
 Screen_Init(320,200,eGRAPHIC_COLOURMODE_4PLANE,0);
 if(!Screen_GetpMemBase()){Platform_DeInit();return 1;}
#ifndef WEDGES_REALTIME
 if(!Wedges_BuildFrames()){Screen_DeInit();Platform_DeInit();return 1;}
#endif
 gWedgesHasBlitter=System_GetBLT()==BLT_BLITTER;
#ifndef WEDGES_REALTIME
 gWedgesBlitter=gWedgesHasBlitter;
#endif
 Memory_Clear(32000,Screen_GetpLogic());Memory_Clear(32000,Screen_GetpPhysic());
#ifdef WEDGES_REALTIME
 Font8x8_PrintColourCanvas("ASM LIVE P PAUSE R REVERSE UP/DN ESC",Screen_GetpLogicGraphic(),0,192,2);
#else
 Font8x8_PrintColourCanvas("P PAUSE R REVERSE UP/DN SPEED B BLT ESC",Screen_GetpLogicGraphic(),0,192,2);
#endif
 Memory_Copy(32000,Screen_GetpLogic(),Screen_GetpPhysic());
 Video_SetPalST(sPalette);
#ifdef WEDGES_REALTIME
 {U16 page,i;for(page=0;page<2;++page)for(i=2;i<1202;i+=2)gWedgesHistory[page][i]=65535;}
 /* Prime the two actual display pages, without building any frame cache.
    Initial edge records represent the initially blank plane; warm-up is outside VBL rendering. */
 Wedges_Live(Screen_GetpLogic(),gWedgesHistory[Screen_GetLogicIndex()],0,0);
 Wedges_Live(Screen_GetpPhysic(),gWedgesHistory[Screen_GetLogicIndex()^1],0,0);
 sPageFrame[0]=sPageFrame[1]=0;
#endif
 gWedgesReady=1;
 while(!quit){
  U32 now;Screen_Update();IKBD_Update();now=Vbl_GetCounter();
  if(gWedgesFrames && now-gWedgesLastVbl>1){
   gWedgesMissedVbl+=now-gWedgesLastVbl-1;
#ifdef WEDGES_REALTIME
   ++gWedgesLate[gWedgesDrawFrame];
#endif
  }
  gWedgesLastVbl=now;
  while(IKBD_GetKbdBytesWaiting()){
   U8 key=IKBD_PopKbdByte();
   if(key==eIKBDSCAN_ESC)quit=1;
   if(key==eIKBDSCAN_P || key==eIKBDSCAN_SPACE)gWedgesPause^=1;
   if(key==eIKBDSCAN_R)gWedgesDirection=-gWedgesDirection;
   if(key==eIKBDSCAN_UPARROW && gWedgesSpeed<16)++gWedgesSpeed;
   if(key==eIKBDSCAN_DOWNARROW && gWedgesSpeed>1)--gWedgesSpeed;
#ifndef WEDGES_REALTIME
   if(key==eIKBDSCAN_B && gWedgesHasBlitter){gWedgesBlitter^=1;sPageFrame[0]=sPageFrame[1]=65535;}
#endif
  }
  Wedges_Render();++gWedgesFrames;Wedges_FrameDone();
  if(!gWedgesPause){
   next=(S16)gWedgesAngle+gWedgesDirection*(S16)gWedgesSpeed;
   if(next<0)next+=1536;
   if(next>=1536)next-=1536;
   gWedgesAngle=(U16)next;
  }
 }
#ifndef WEDGES_REALTIME
 _Memory_Release(gWedgesCache);gWedgesCache=0;
#endif
 Screen_DeInit();Platform_DeInit();gWedgesExited=1;return 0;
}
