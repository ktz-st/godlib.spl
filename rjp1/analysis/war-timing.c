/* Test-only wrapper around the real release UI/audio callback. No disk/debugger
 * accesses during the measured window. PAL 200Hz clock gives 5ms bins. */
#include <godlib/music/rjp1.h>
#include <godlib/vbl/vbl.h>
#include <godlib/system/system.h>
#include <godlib/file/file.h>
#include <godlib/music/paulamixer.h>
#include <string.h>
#define COUNT 15000
volatile U32 gWarTicks,gWarMaxGap,gWarMaxCost,gWarLongGaps,gWarOverruns;
volatile U16 gWarDone;
U16 gWarGapBins[32],gWarCostBins[32];
static U32 previous;
static void timing(void)
{
 U32 now,delta,cost;
 if(gWarDone){Rjp1_Tick();return;}
 now=*(volatile U32*)0x4baUL;delta=previous?now-previous:4;
 previous=now;
 if(delta>gWarMaxGap)gWarMaxGap=delta;
 if(delta>=6)++gWarLongGaps;
 ++gWarGapBins[delta<32?delta:31];
 Rjp1_Tick();
 cost=*(volatile U32*)0x4baUL-now;
 if(cost>gWarMaxCost)gWarMaxCost=cost;
 if(cost>=4)++gWarOverruns;
 ++gWarCostBins[cost<32?cost:31];
 if(++gWarTicks>=COUNT)gWarDone=1;
}
static U8 TimedStart(sRjp1Song *song,U16 sub,U8 rate)
{
 U8 ok;U16 mask;
 mask=System_GetIML();System_SetIML(7);Vbl_RemoveCall(timing);System_SetIML(mask);
 ok=Rjp1_Start(song,sub,rate);
 if(ok){gWarTicks=gWarMaxGap=gWarMaxCost=gWarLongGaps=gWarOverruns=previous=0;gWarDone=0;memset(gWarGapBins,0,sizeof(gWarGapBins));memset(gWarCostBins,0,sizeof(gWarCostBins));mask=System_GetIML();System_SetIML(7);Vbl_RemoveCall(Rjp1_Tick);Vbl_AddCall(timing);System_SetIML(mask);}
 return ok;
}
#define Rjp1_Start TimedStart
#include "../rjp1.c"
