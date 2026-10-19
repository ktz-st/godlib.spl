/* Compile the production implementation here to test its internal refill path. */
#include "../../../godlib/audio/amixer.c"
#include <godlib/platform/platform.h>
#include <godlib/gemdos/gemdos.h>
#include <godlib/ikbd/ikbd.h>
#include <godlib/screen/screen.h>
#define CASES 105
U8 gMixOutput[CASES][512],gMixSpecial[8][512],gMixLow[8][512],gMixSingle[2][512],gMixPairs[4][131072];
volatile U16 gMixReady,gMixLive,gMixExit,gMixError,gMixHeartbeat;
static U8 pair0[65537],pair1[65537];
static U8 source[258],shortSource[4]={127,128,37,99};
static U8 volumes[7]={0,1,64,127,128,254,255},pans[5]={0,64,128,192,255};
void __attribute__((noinline)) MixCheck_Marker(void){__asm__ volatile("");}
S16 GodLib_Game_Main(S16 argc,char **argv)
{
 U32 offset;U16 count;
 U16 i,j,k,n=0; sAudioDmaSound s; sAmixerConfig config;
 (void)argc;(void)argv;GemDos_Super(0);Platform_Init();AudioMixer_Init();
 for(i=0;i<258;++i)source[i]=(U8)(i-1); /* odd-aligned source, all 256 values */
 s.mpSound=source+1;s.mLength=256;s.mFreq=eAUDIO_FREQ_25;
 s.mBits=eAUDIO_BITS_8;s.mStereoFlag=0;s.mLoopingFlag=0;
 config=*AudioMixer_GetpConfig();
 for(k=0;k<3;++k){
  gAudioMixerEnableFlag=0;config.mPanType=k;AudioMixer_SetConfig(&config);
  gAudioMixerEnableFlag=1;
  for(i=0;i<7;++i)for(j=0;j<5;++j){
   AudioMixer_StopVoice(1);
   if(!AudioMixer_PlayVoice(0,&s,volumes[i],pans[j]))gMixError|=1;
   fill(gMixOutput[n++],256);
   if(AudioMixer_IsVoicePlaying(0))gMixError|=2;
  }
 }
 config.mPanType=0;gAudioMixerEnableFlag=0;AudioMixer_SetConfig(&config);gAudioMixerEnableFlag=1;
 /* Equal positive/negative extreme inputs: clipping must saturate, not wrap. */
 for(i=0;i<256;++i)source[i+1]=(i&1)?128:127;
 AudioMixer_PlayVoice(0,&s,255,0);AudioMixer_PlayVoice(1,&s,255,0);fill(gMixSpecial[0],256);
 /* Odd 3-byte source followed by nonzero guard. One-shot ends exactly. */
 s.mpSound=shortSource;s.mLength=3;s.mFreq=eAUDIO_FREQ_12;
 AudioMixer_PlayVoice(0,&s,255,255);fill(gMixSpecial[1],256);
 if(AudioMixer_IsVoicePlaying(0))gMixError|=4;
 /* Loop crossing and partial duplicated source frames across fill calls. */
 s.mLoopingFlag=1;AudioMixer_PlayVoice(0,&s,255,0);
 fill(gMixSpecial[2],3);fill(gMixSpecial[2]+6,253);
 AudioMixer_SetVoiceParams(0,128,128);fill(gMixSpecial[3],256);
 AudioMixer_StopVoice(0);fill(gMixSpecial[4],256);
 s.mFreq=eAUDIO_FREQ_6;AudioMixer_PlayVoice(0,&s,255,0);fill(gMixSpecial[5],256);
 AudioMixer_StopVoice(0);
 s.mFreq=eAUDIO_FREQ_50;if(AudioMixer_PlayVoice(0,&s,255,0))gMixError|=8;
 s.mFreq=eAUDIO_FREQ_25;s.mStereoFlag=1;if(AudioMixer_PlayVoice(0,&s,255,0))gMixError|=16;
 s.mStereoFlag=0;s.mBits=eAUDIO_BITS_16;if(AudioMixer_PlayVoice(0,&s,255,0))gMixError|=32;
 s.mBits=eAUDIO_BITS_8;s.mLength=0;if(AudioMixer_PlayVoice(0,&s,255,0))gMixError|=64;
 s.mLength=3;if(AudioMixer_PlayVoice(2,&s,255,0))gMixError|=128;
 /* Legacy wrappers: 2 slots, normal rejects full, Direct steals. */
 AudioMixer_PlaySample(&s,0);AudioMixer_PlaySample(&s,255);
 if(AudioMixer_PlaySample(&s,128)||AudioMixer_CanPlayNewSpl())gMixError|=256;
 if(!AudioMixer_PlaySampleDirect(&s,128))gMixError|=512;
 /* Exercise the lone second voice and odd unrolled-loop tails. */
 AudioMixer_StopVoice(0);AudioMixer_StopVoice(1);
 s.mpSound=source+1;s.mLength=256;s.mLoopingFlag=0;s.mFreq=eAUDIO_FREQ_25;
 AudioMixer_PlayVoice(1,&s,192,192);fill(gMixSingle[0],3);fill(gMixSingle[0]+6,253);
 s.mFreq=eAUDIO_FREQ_12;AudioMixer_PlayVoice(1,&s,192,192);fill(gMixSingle[1],255);fill(gMixSingle[1]+510,1);
 /* All 65536 signed-byte input pairs, left and right clipping independently.
    257-frame chunks exercise odd prologues as well as unrolled pairs. */
 for(offset=0;offset<65536UL;++offset){pair0[offset+1]=(U8)(offset>>8);pair1[offset+1]=(U8)offset;}
 for(k=0;k<4;++k) {
  AudioMixer_StopVoice(0);AudioMixer_StopVoice(1);
  s.mpSound=pair0+1;s.mLength=65536UL;s.mFreq=eAUDIO_FREQ_25;s.mLoopingFlag=0;
  AudioMixer_PlayVoice(0,&s,k==2?128:255,k==1?255:(k==3?128:0));s.mpSound=pair1+1;AudioMixer_PlayVoice(1,&s,k==2?128:255,k==1?255:(k==3?128:0));
  for(offset=0;offset<65536UL;offset+=count){count=65536UL-offset>257?257:(U16)(65536UL-offset);fill(gMixPairs[k]+offset*2,count);}
 }
 /* Low-rate conversion and controls, using the exact same production core. */
 gAudioMixerEnableFlag=0;
 if(!AudioMixer_SetFrequency(eAUDIO_FREQ_12) || gAudioMixerEnableFlag || AudioMixer_GetFrequency()!=eAUDIO_FREQ_12)gMixError|=2048;
 gAudioMixerEnableFlag=1;
 for(i=0;i<256;++i)source[i+1]=(U8)i;
 s.mpSound=source+1;s.mLength=256;s.mFreq=eAUDIO_FREQ_25;s.mLoopingFlag=0;
 AudioMixer_StopVoice(1);AudioMixer_PlayVoice(0,&s,255,0);fill(gMixLow[0],256);
 if(AudioMixer_IsVoicePlaying(0))gMixError|=4096;
 s.mpSound=shortSource;s.mLength=3;s.mLoopingFlag=1;
 AudioMixer_PlayVoice(0,&s,255,255);fill(gMixLow[1],1);fill(gMixLow[1]+2,255);
 s.mFreq=eAUDIO_FREQ_6;AudioMixer_PlayVoice(0,&s,255,0);fill(gMixLow[2],3);fill(gMixLow[2]+6,253);
 s.mpSound=source+1;s.mLength=256;s.mFreq=eAUDIO_FREQ_12;s.mLoopingFlag=0;
 AudioMixer_PlayVoice(0,&s,255,128);fill(gMixLow[3],256);
 AudioMixer_PlayVoice(0,&s,128,192);fill(gMixLow[4],256);
 s.mpSound=shortSource;s.mLength=3;s.mLoopingFlag=1;s.mFreq=eAUDIO_FREQ_6;
 AudioMixer_PlayVoice(0,&s,200,32);s.mFreq=eAUDIO_FREQ_25;AudioMixer_PlayVoice(1,&s,180,224);
 fill(gMixLow[5],1);fill(gMixLow[5]+2,255);
 s.mLength=1;AudioMixer_PlayVoice(0,&s,255,0);AudioMixer_StopVoice(1);fill(gMixLow[6],256);
 AudioMixer_StopVoice(0);AudioMixer_StopVoice(1);
 s.mpSound=source+1;s.mLength=256;s.mFreq=eAUDIO_FREQ_25;s.mLoopingFlag=0;
 AudioMixer_PlayVoice(1,&s,64,64);fill(gMixLow[7],256);
 s.mpSound=shortSource;s.mLength=3;s.mLoopingFlag=1;
 AudioMixer_PlayVoice(0,&s,255,0);AudioMixer_PlayVoice(1,&s,180,224);
 if(!AudioMixer_SetFrequency(eAUDIO_FREQ_12) || !AudioMixer_IsVoicePlaying(0) || !AudioMixer_IsVoicePlaying(1))gMixError|=8192;
 if(AudioMixer_SetFrequency(eAUDIO_FREQ_6) || AudioMixer_SetFrequency(eAUDIO_FREQ_50) || AudioMixer_GetFrequency()!=eAUDIO_FREQ_12)gMixError|=8192;
 gAudioMixerEnableFlag=0;AudioMixer_SetFrequency(eAUDIO_FREQ_25);
 if(gAudioMixerEnableFlag || AudioMixer_IsVoicePlaying(0) || AudioMixer_IsVoicePlaying(1))gMixError|=16384;
 for(i=0;i<256;++i)source[i+1]=(i&1)?128:127;
 gAudioMixerEnableFlag=0;AudioMixer_Enable();
 s.mpSound=source+1;s.mLength=256;s.mLoopingFlag=1;s.mFreq=eAUDIO_FREQ_25;
 AudioMixer_PlayVoice(0,&s,180,32);AudioMixer_PlayVoice(1,&s,200,224);
 gMixReady=1;
 while(!gMixLive){Vbl_WaitVbl();gMixHeartbeat++;MixCheck_Marker();}
 /* Switch the actual running DMA engine; reset sources and queued audio. */
 if(!AudioMixer_SetFrequency(eAUDIO_FREQ_12) || !gAudioMixerEnableFlag || AudioMixer_IsVoicePlaying(0) || AudioMixer_IsVoicePlaying(1) || (HW8(0xffff8921UL)&3)!=eAUDIO_FREQ_12)gMixError|=32768;
 for(i=0;i<RING;++i)if(gpAudioMixerBuffer[i])gMixError|=32768;
 AudioMixer_PlayVoice(0,&s,180,32);AudioMixer_PlayVoice(1,&s,200,224);
 gMixLive=0;gMixReady=2;
 while(!gMixLive){Vbl_WaitVbl();gMixHeartbeat++;MixCheck_Marker();}
 if(!AudioMixer_SetFrequency(eAUDIO_FREQ_25) || (HW8(0xffff8921UL)&3)!=eAUDIO_FREQ_25)gMixError|=32768;
 AudioMixer_Disable();AudioMixer_DeInit();AudioMixer_Init();AudioMixer_Enable();
 s.mLoopingFlag=0;AudioMixer_PlayVoice(0,&s,255,128);
 for(i=0;i<20;++i)Vbl_WaitVbl();
 if(AudioMixer_IsVoicePlaying(0))gMixError|=1024;
 for(i=0;i<8192;++i)if(gpAudioMixerBuffer[i])gMixError|=1024;
 AudioMixer_DeInit();Platform_DeInit();gMixExit=1;MixCheck_Marker();return 0;
}
