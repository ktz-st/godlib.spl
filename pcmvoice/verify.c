#include <godlib/audio/pcmvoice.h>
/* ABI-level core tests run before the public mixer owns DMA. */
typedef struct {const S8 *data;U32 length;U8 priority,pad;} Sample;
typedef struct {const Sample *sample;const S8 *current,*end;const Sample *next;U8 loop,active,priority,pad;} Channel;
typedef struct {Channel *channels;S8 *dst,*silence;U16 count,saturate;} Params;
extern void PcmVoiceMixer_CoreFill(Params*);
extern U16 PcmVoiceMixer_RefillCount(U16 write,U16 offset);
static U16 buffer[514],silent[125],large[33000],small[3][5];
static U16 saturate;
static Sample samples[4];static Channel channels[3];
volatile U16 gPacmadVerifyCases,gPacmadVerifyFailures;
static void reset(void)
{
 U16 i;for(i=0;i<3;++i){channels[i].sample=channels[i].next=0;channels[i].active=0;channels[i].loop=1;channels[i].current=(S8*)silent;channels[i].end=(S8*)silent+250;}
}
static void source(U16 ch,Sample *s,U8 loop)
{channels[ch].sample=s;channels[ch].current=s->data;channels[ch].end=s->data+s->length;channels[ch].loop=loop;channels[ch].active=1;}
static void fill(U16 count)
{Params p;U16 i;for(i=0;i<514;++i)buffer[i]=0xa55a;p.channels=channels;p.dst=(S8*)(buffer+1);p.silence=(S8*)silent;p.count=count;p.saturate=saturate;PcmVoiceMixer_CoreFill(&p);}
static void check(U16 count,U8 value)
{U16 i;if(buffer[0]!=0xa55a || buffer[1+count/2]!=0xa55a)++gPacmadVerifyFailures;for(i=0;i<count;++i)if(((U8*)(buffer+1))[i]!=value){++gPacmadVerifyFailures;break;}
 ++gPacmadVerifyCases;}
U16 PcmVoiceMix_Verify(void)
{
 U16 i,ch,count;U32 f,sum,consumed;U16 write,n;
 for(i=0;i<125;++i)silent[i]=0;
 for(i=0;i<33000;++i)large[i]=0x0505;
 for(ch=0;ch<3;++ch){for(i=0;i<5;++i)small[ch][i]=(U16)(1+ch*2)*257;samples[ch].data=(S8*)small[ch];samples[ch].length=2+ch*4;}
 samples[3].data=(S8*)large;samples[3].length=65536UL;
 reset();fill(250);check(250,0);
 reset();source(0,&samples[3],0);fill(250);check(250,5); /* exact 64K remaining */
 reset();samples[3].length=66000UL;source(2,&samples[3],0);
 for(i=0;i<264;++i){fill(250);check(250,5);}fill(250);check(250,0);
 reset();for(ch=0;ch<3;++ch)source(ch,&samples[ch],1);
 for(count=250;count<=252;count+=2){fill(count);check(count,9);}fill(500);check(500,9);
 reset();samples[0].length=6;samples[1].length=4;for(i=0;i<5;++i)small[1][i]=0x0707;
 source(0,&samples[0],0);channels[0].next=&samples[1];fill(250);
 for(i=0;i<250;++i)if(((U8*)(buffer+1))[i]!=(i<6?1:i<10?7:0)){++gPacmadVerifyFailures;break;}
 ++gPacmadVerifyCases;
 if(channels[0].active || channels[0].next)++gPacmadVerifyFailures;
 /* Explicit packed-carry behavior, followed by independent byte tail. */
 reset();small[0][0]=0;small[0][1]=0x00ff;small[1][0]=0;small[1][1]=1;
 samples[0].length=samples[1].length=4;source(0,&samples[0],0);source(1,&samples[1],0);fill(4);
 if(buffer[1]!=0 || buffer[2]!=0x0100)++gPacmadVerifyFailures;
 ++gPacmadVerifyCases;
 /* Saturation applies once to the full signed sum, including cancellation.
  * Exercise both tails and source boundaries, with varied signed PCM. */
 {
  static const S8 values[6]={-128,-100,-1,0,100,127};
  U16 a,b,c;S16 total;
  saturate=1;
  for(a=0;a<6;++a)for(b=0;b<6;++b)for(c=0;c<6;++c){
   U8 v[3];v[0]=(U8)values[a];v[1]=(U8)values[b];v[2]=(U8)values[c];
   reset();
   for(ch=0;ch<3;++ch){
    for(i=0;i<5;++i)small[ch][i]=(U16)v[ch]*257u;
    samples[ch].length=2+ch*4;source(ch,&samples[ch],1);
   }
   total=(S16)values[a]+values[b]+values[c];
   if(total>127)total=127;else if(total<-128)total=-128;
   fill(252);check(252,(U8)total);
  }
  reset();
  for(ch=0;ch<3;++ch){
   for(i=0;i<10;++i)((S8*)small[ch])[i]=(S8)(i*37+ch*83);
   samples[ch].length=2+ch*4;source(ch,&samples[ch],1);
  }
  fill(500);
  for(i=0;i<500;++i){
   total=0;for(ch=0;ch<3;++ch)total+=((S8*)small[ch])[i%(2+ch*4)];
   if(total>127)total=127;else if(total<-128)total=-128;
   if(((S8*)(buffer+1))[i]!=total){++gPacmadVerifyFailures;break;}
  }
  if(buffer[0]!=0xa55a || buffer[251]!=0xa55a)++gPacmadVerifyFailures;
  ++gPacmadVerifyCases;
  reset();source(0,&samples[0],1);fill(252);
  for(i=0;i<252;++i)if(((S8*)(buffer+1))[i]!=((S8*)small[0])[i%2]){++gPacmadVerifyFailures;break;}
  if(buffer[0]!=0xa55a || buffer[127]!=0xa55a)++gPacmadVerifyFailures;
  ++gPacmadVerifyCases;saturate=0;
 }
 /* 40 seconds of 12517-Hz consumption, with one missed VBL every 101.
  * Total source advancement must equal consumed bytes, rather than 250/VBL. */
 write=640;sum=0;
 for(f=1;f<=2000;++f){if(f%101==0)continue;consumed=f*12517UL/50UL;n=PcmVoiceMixer_RefillCount(write,(U16)(consumed&1023UL));if(n>576)++gPacmadVerifyFailures;sum+=n;write=(write+n)&1023;if(sum!=(consumed&~1UL))++gPacmadVerifyFailures;}
 ++gPacmadVerifyCases;return gPacmadVerifyFailures;
}
