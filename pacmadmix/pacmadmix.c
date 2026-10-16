#include <godlib/audio/pacmadmix.h>
#include <godlib/font8x8/font8x8.h>
#include <godlib/gemdos/gemdos.h>
#include <godlib/ikbd/ikbd.h>
#include <godlib/platform/platform.h>
#include <godlib/screen/screen.h>
#include <godlib/video/video.h>
#include <godlib/vbl/vbl.h>
extern U16 PacmadMix_Verify(void);
static U16 pcm[3][4096];
static U16 palette[16]={0,0x777};
volatile U16 gPacmadMixReady,gPacmadMixExited;
S16 GodLib_Game_Main(S16 argc,char **argv)
{
 U16 i,ch,page,test;U8 quit=0,raster=0;
 (void)argc;(void)argv;GemDos_Super(0);Platform_Init();test=PacmadMix_Verify();
 /* Quiet synthetic signed PCM, already at 12517 Hz; no asset dependencies. */
 for(ch=0;ch<3;++ch)for(i=0;i<4096;++i) {S8 v=(i/(12+ch*7)&1)?12:-12;pcm[ch][i]=(U16)(U8)v*257;}
 Screen_Init(320,200,eGRAPHIC_COLOURMODE_4PLANE,eSCREEN_SCROLL_NONE);Video_SetPalST(palette);
 gPacmadMixReady=!test && PacmadMixer_Init();
 for(page=0;page<2;++page){U16 *p;
  if(page){Screen_Physic_ClearScreen();p=Screen_GetpPhysic();}else{Screen_Logic_ClearScreen();p=Screen_GetpLogic();}
  Font8x8_Print("PacMad mixer / GodLib",p,8,8);
  Font8x8_Print("3 channels - 12.5 kHz mono",p,8,24);
  Font8x8_Print(test?"Core/scheduler test FAILED":"Core/scheduler test PASS",p,8,40);
  Font8x8_Print(gPacmadMixReady?"DMA ready":"DMA init failed",p,8,56);
  Font8x8_Print("F1-F3: toggle channel loop",p,8,80);
  Font8x8_Print("F4: three one-shots",p,8,96);
  Font8x8_Print("F5: one-shot + queued sample",p,8,112);
  Font8x8_Print("F6: stop / F9: CPU raster",p,8,128);
  Font8x8_Print("ESC: quit",p,8,152);
 }
 Screen_Update();
 while(!quit){Vbl_WaitVbl();IKBD_Update();while(IKBD_GetKbdBytesWaiting()){
  U8 key=IKBD_PopKbdByte();
  if(key==eIKBDSCAN_ESC)quit=1;
  if(key==eIKBDSCAN_F9){raster^=1;PacmadMixer_SetRasterDebug(raster);}
  if(!gPacmadMixReady)continue;
  if(key>=eIKBDSCAN_F1 && key<=eIKBDSCAN_F3){ch=key-eIKBDSCAN_F1;if(PacmadMixer_IsPlaying(ch))PacmadMixer_Stop(ch);else PacmadMixer_Play(ch,(S8*)pcm[ch],sizeof(pcm[ch]),1);}
  if(key==eIKBDSCAN_F4)for(ch=0;ch<3;++ch)PacmadMixer_Play(ch,(S8*)pcm[ch],sizeof(pcm[ch]),0);
  if(key==eIKBDSCAN_F5){PacmadMixer_Play(0,(S8*)pcm[0],sizeof(pcm[0]),0);PacmadMixer_Queue(0,(S8*)pcm[1],sizeof(pcm[1]));}
  if(key==eIKBDSCAN_F6)PacmadMixer_StopAll();
 }}
 /* Restore TOS video and remove VBL users before freeing screen storage. */
 PacmadMixer_DeInit();Platform_DeInit();Screen_DeInit();gPacmadMixExited=1;return 0;
}
