/* Exercise the actual 68000 mixer, not a host imitation. Run before Init. */
#include <godlib/audio/sgdlmix.h>
typedef struct { const S8 *current,*end,*loop; } sChannel;
extern sChannel gSgdlMixerChannels[4];
extern void SgdlMixer_MixBlock(S8 * output);
static S8 sInput[4][1024];
static S8 sOutput[514];
volatile U16 gSgdlMixTestResult;

U16 SgdlMix_Verify(void)
{
    U16 mask,i,j;
    for(j=0;j<4;++j)
        for(i=0;i<1024;++i) sInput[j][i]=(S8)(i*(j+1)+j*71);
    for(mask=0;mask<16;++mask) {
        for(j=0;j<4;++j) {
            gSgdlMixerChannels[j].current=(mask&(1<<j))?sInput[j]:0;
            gSgdlMixerChannels[j].end=(mask&(1<<j))?sInput[j]+512:0;
            gSgdlMixerChannels[j].loop=0;
        }
        sOutput[0]=81; sOutput[513]=82;
        SgdlMixer_MixBlock(sOutput+1);
        if(sOutput[0]!=81 || sOutput[513]!=82) return (gSgdlMixTestResult=1);
        for(i=0;i<512;++i) {
            S16 sum=0;
            for(j=0;j<4;++j) if(mask&(1<<j)) sum+=sInput[j][i];
            if((U8)sOutput[i+1]!=(U8)sum) return (gSgdlMixTestResult=2);
        }
        for(j=0;j<4;++j)
            if(gSgdlMixerChannels[j].current || gSgdlMixerChannels[j].end)
                return (gSgdlMixTestResult=3);
    }
    for(j=0;j<4;++j) {
        gSgdlMixerChannels[j].current=sInput[j];
        gSgdlMixerChannels[j].end=sInput[j]+1024;
        gSgdlMixerChannels[j].loop=sInput[j];
    }
    SgdlMixer_MixBlock(sOutput+1);
    for(j=0;j<4;++j)
        if(gSgdlMixerChannels[j].current!=sInput[j]+512) return (gSgdlMixTestResult=4);
    SgdlMixer_MixBlock(sOutput+1);
    for(j=0;j<4;++j) {
        if(gSgdlMixerChannels[j].current!=sInput[j]) return (gSgdlMixTestResult=5);
        gSgdlMixerChannels[j].current=gSgdlMixerChannels[j].end=gSgdlMixerChannels[j].loop=0;
    }
    gSgdlMixTestResult=0;
    return 0;
}
