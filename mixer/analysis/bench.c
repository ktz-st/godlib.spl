#include <godlib/audio/amixer.h>
#include <godlib/platform/platform.h>
#include <godlib/gemdos/gemdos.h>
#include <godlib/ikbd/ikbd.h>
volatile U16 gBenchCase=0,gBenchReady=0xffff;
static U8 source[32768];
static void setup(U16 index)
{
 U16 count,rate,sourceRate,ch; sAudioDmaSound sound;
 AudioMixer_Disable();
 rate=index<3?eAUDIO_FREQ_12:eAUDIO_FREQ_25;count=index<3?index:index-3;
 if(index==6){rate=eAUDIO_FREQ_25;count=2;sourceRate=eAUDIO_FREQ_12;}
 else if(index==7){rate=eAUDIO_FREQ_12;count=2;sourceRate=eAUDIO_FREQ_25;}
 else if(index>=8){rate=index==8?eAUDIO_FREQ_12:eAUDIO_FREQ_25;count=2;sourceRate=rate;}
 else sourceRate=rate;
 AudioMixer_SetFrequency(rate);AudioMixer_Enable();
 sound.mLength=32749;sound.mFreq=sourceRate;sound.mBits=eAUDIO_BITS_8;sound.mStereoFlag=0;sound.mLoopingFlag=1;
 for(ch=0;ch<count;++ch){sound.mpSound=source+ch*3;AudioMixer_PlayVoice(ch,&sound,index>=8?255:(ch?190:220),index>=8?0:(ch?224:32));}
 gBenchReady=index;
}
S16 GodLib_Game_Main(S16 argc,char **argv)
{
 U16 i;(void)argc;(void)argv;GemDos_Super(0);Platform_Init();AudioMixer_Init();
 for(i=0;i<32768;++i)source[i]=(U8)((i*37U)^(i>>4));
 for(;;)if(gBenchReady!=gBenchCase)setup(gBenchCase);
}
