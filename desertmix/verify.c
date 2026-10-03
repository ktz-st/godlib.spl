/* State slab uses the original byte offsets (-fno-strict-aliasing).
 * Target-side checks execute the original 68000 mixing routine. */
#include <godlib/base/base.h>
extern U16 gDesertMixerState[];
extern void DesertMixer_CoreFill(U32 offset,U32 count);
#define BYTE(a) (*(volatile U8 *)((U8 *)gDesertMixerState+(a)-0x2da74UL))
#define LONG(a) (*(volatile U32 *)((U8 *)gDesertMixerState+(a)-0x2da74UL))
static U16 sInput[4][128];
volatile U16 gDesertMixTestResult;
U16 DesertMix_Verify(void)
{
    U16 i,j,mask;
    U8 *out=(U8 *)gDesertMixerState+0x118;
    for(j=0;j<4;++j) for(i=0;i<256;++i) ((U8 *)sInput[j])[i]=(U8)(i*(j+1)+j*71);
    for(mask=0;mask<16;++mask) {
        LONG(0x2db80)=(U32)sInput[0];LONG(0x2db84)=256;LONG(0x2da90)=0;
        BYTE(0x2db2c)=!(mask&1);
        LONG(0x2da7c)=(mask&2)?(U32)sInput[1]:0;
        LONG(0x2da78)=256;LONG(0x2da74)=0;
        LONG(0x2da80)=(U32)sInput[2];LONG(0x2da84)=(mask&4)?64:0;
        LONG(0x2da88)=(U32)sInput[3];LONG(0x2da8c)=(mask&8)?64:0;
        out[0]=81;out[68]=82;
        DesertMixer_CoreFill(4,64);
        if(out[0]!=81 || out[68]!=82) return (gDesertMixTestResult=1);
        for(i=0;i<64;++i) {
            U16 sum=0;
            for(j=0;j<4;++j) if(mask&(1<<j)) sum+=((U8 *)sInput[j])[i];
            if(out[4+i]!=(U8)sum) return (gDesertMixTestResult=2);
        }
        if(LONG(0x2da84) || LONG(0x2da8c)) return (gDesertMixTestResult=3);
    }
    /* Multiple loop wraps, partial one-shot endings within a refill. */
    BYTE(0x2db2c)=0;LONG(0x2da90)=8;LONG(0x2db84)=12;
    LONG(0x2da7c)=(U32)sInput[1];LONG(0x2da78)=20;LONG(0x2da74)=16;
    LONG(0x2da80)=(U32)sInput[2];LONG(0x2da84)=24;
    LONG(0x2da88)=(U32)sInput[3];LONG(0x2da8c)=32;
    DesertMixer_CoreFill(4,64);
    for(i=0;i<64;++i) {
        U16 sum=((U8 *)sInput[0])[(i+8)%12]+((U8 *)sInput[1])[(i+16)%20];
        if(i<24) sum+=((U8 *)sInput[2])[i];
        if(i<32) sum+=((U8 *)sInput[3])[i];
        if(out[4+i]!=(U8)sum) return (gDesertMixTestResult=4);
    }
    if(LONG(0x2da90)!=0 || LONG(0x2da74)!=0 || LONG(0x2da84) || LONG(0x2da8c))
        return (gDesertMixTestResult=5);
    gDesertMixTestResult=0;
    return 0;
}
