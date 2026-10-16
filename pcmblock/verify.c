/* Exercise the actual 68000 mixer, not a host imitation. Run before Init. */
#include <godlib/audio/pcmblock.h>
typedef struct { const S8 *current,*end,*loop; } sChannel;
extern sChannel gPcmBlockMixerChannels[4];
extern void PcmBlockMixer_MixBlock(S8 * output);
static S8 sInput[4][1024];
static S8 sOutput[514];
volatile U16 gPcmBlockMixTestResult;

U16 PcmBlockMix_Verify(void)
{
    U16 mask,i,j;
    for(j=0;j<4;++j)
        for(i=0;i<1024;++i) sInput[j][i]=(S8)(i*(j+1)+j*71);
    for(mask=0;mask<16;++mask) {
        for(j=0;j<4;++j) {
            gPcmBlockMixerChannels[j].current=(mask&(1<<j))?sInput[j]:0;
            gPcmBlockMixerChannels[j].end=(mask&(1<<j))?sInput[j]+512:0;
            gPcmBlockMixerChannels[j].loop=0;
        }
        sOutput[0]=81; sOutput[513]=82;
        PcmBlockMixer_MixBlock(sOutput+1);
        if(sOutput[0]!=81 || sOutput[513]!=82) return (gPcmBlockMixTestResult=1);
        for(i=0;i<512;++i) {
            S16 sum=0;
            for(j=0;j<4;++j) if(mask&(1<<j)) sum+=sInput[j][i];
            if((U8)sOutput[i+1]!=(U8)sum) return (gPcmBlockMixTestResult=2);
        }
        for(j=0;j<4;++j)
            if(gPcmBlockMixerChannels[j].current || gPcmBlockMixerChannels[j].end)
                return (gPcmBlockMixTestResult=3);
    }
    for(j=0;j<4;++j) {
        gPcmBlockMixerChannels[j].current=sInput[j];
        gPcmBlockMixerChannels[j].end=sInput[j]+1024;
        gPcmBlockMixerChannels[j].loop=sInput[j];
    }
    PcmBlockMixer_MixBlock(sOutput+1);
    for(j=0;j<4;++j)
        if(gPcmBlockMixerChannels[j].current!=sInput[j]+512) return (gPcmBlockMixTestResult=4);
    PcmBlockMixer_MixBlock(sOutput+1);
    for(j=0;j<4;++j) {
        if(gPcmBlockMixerChannels[j].current!=sInput[j]) return (gPcmBlockMixTestResult=5);
        gPcmBlockMixerChannels[j].current=gPcmBlockMixerChannels[j].end=gPcmBlockMixerChannels[j].loop=0;
    }
    gPcmBlockMixTestResult=0;
    return 0;
}
