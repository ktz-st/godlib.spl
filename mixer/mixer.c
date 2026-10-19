/* AMIXER: two PCM voices, true volume/pan, saturated stereo output. */
#include <godlib/audio/amixer.h>
#include <godlib/file/file.h>
#include <godlib/font8x8/font8x8.h>
#include <godlib/ikbd/ikbd.h>
#include <godlib/platform/platform.h>
#include <godlib/gemdos/gemdos.h>
#include <godlib/screen/screen.h>
#include <godlib/video/video.h>
#include <godlib/system/system.h>
#include <stdio.h>
static S8 tone[128];
static U16 palette[16]={0,0x777};
S16 GodLib_Game_Main(S16 argc,char **argv)
{
 sAudioDmaSound voice,drone;U16 i,volume=192,pan=128,quit=0,toneOn=0,dirty=2;char line[40];
 (void)argc;(void)argv;GemDos_Super(0);Platform_Init();AudioMixer_Init();AudioMixer_Enable();
 Screen_Init(320,200,eGRAPHIC_COLOURMODE_4PLANE,eSCREEN_SCROLL_NONE);
 Video_SetPalST(palette);
 voice.mpSound=File_Load("voice.raw");voice.mLength=File_GetSize("voice.raw");
 voice.mBits=eAUDIO_BITS_8;voice.mFreq=eAUDIO_FREQ_12;voice.mStereoFlag=0;voice.mLoopingFlag=0;
 for(i=0;i<128;++i)tone[i]=(S8)(i<64?(S16)i*2-64:192-(S16)i*2);
 drone.mpSound=(U8*)tone;drone.mLength=128;drone.mBits=eAUDIO_BITS_8;
 drone.mFreq=eAUDIO_FREQ_25;drone.mStereoFlag=0;drone.mLoopingFlag=1;
 AudioMixer_PlayVoice(0,&voice,volume,pan);
 while(!quit) {
  Screen_Update();IKBD_Update();
  while(IKBD_GetKbdBytesWaiting()) {
   U8 key=IKBD_PopKbdByte();
   switch(key) {
   case eIKBDSCAN_ESC:quit=1;break;
   case eIKBDSCAN_SPACE:AudioMixer_PlayVoice(0,&voice,volume,pan);break;
   case eIKBDSCAN_F1:pan=0;break;
   case eIKBDSCAN_F2:pan=128;break;
   case eIKBDSCAN_F3:pan=255;break;
   case eIKBDSCAN_LEFTARROW:pan=pan>16?pan-16:0;break;
   case eIKBDSCAN_RIGHTARROW:pan=pan<239?pan+16:255;break;
   case eIKBDSCAN_UPARROW:volume=volume<239?volume+16:255;break;
   case eIKBDSCAN_DOWNARROW:volume=volume>16?volume-16:0;break;
   case eIKBDSCAN_F4:
    AudioMixer_SetFrequency(AudioMixer_GetFrequency()==eAUDIO_FREQ_25?eAUDIO_FREQ_12:eAUDIO_FREQ_25);
    AudioMixer_PlayVoice(0,&voice,volume,pan);
    if(toneOn)AudioMixer_PlayVoice(1,&drone,128,128);
    break;
   case eIKBDSCAN_2:
    toneOn^=1;if(toneOn)AudioMixer_PlayVoice(1,&drone,128,128);else AudioMixer_StopVoice(1);break;
   default:continue;
   }
   AudioMixer_SetVoiceParams(0,volume,pan);dirty=2;
  }
  if(dirty) {
   void *screen=Screen_GetpLogic();Screen_Logic_ClearScreen();
   Font8x8_Print("AMIXER / VOLUME + PAN",screen,0,8);
   Font8x8_Print("SPACE: PLAY  2: LOOPING SECOND VOICE",screen,0,32);
   Font8x8_Print("UP/DOWN: VOLUME  LEFT/RIGHT: PAN",screen,0,48);
   Font8x8_Print("F1: LEFT  F2: CENTRE  F3: RIGHT",screen,0,64);
   Font8x8_Print("ESC: EXIT",screen,0,80);
   sprintf(line,"VOLUME %3u / 255   PAN %3u / 255",volume,pan);
   Font8x8_Print(line,screen,0,104);
   Font8x8_Print(toneOn?"SECOND VOICE: ON":"SECOND VOICE: OFF",screen,0,120);
   Font8x8_Print(AudioMixer_GetFrequency()==eAUDIO_FREQ_25?"25 KHZ STEREO / TWO PCM VOICES":"12.5 KHZ STEREO / TWO PCM VOICES",screen,0,144);
   Font8x8_Print("F4: SWITCH 12.5 / 25 KHZ",screen,0,160);
   if(!voice.mpSound)Font8x8_Print("MISSING VOICE.RAW",screen,0,176);
   if(System_GetMCH()==MCH_ST)Font8x8_Print("DMA AUDIO REQUIRES STE",screen,0,184);
   --dirty;
  }
 }
 AudioMixer_DeInit();if(voice.mpSound)File_UnLoad(voice.mpSound);
 Screen_DeInit();Platform_DeInit();return 0;
}
