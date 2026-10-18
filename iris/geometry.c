/* Adapted from superhex_ste/src/main.c iris_fill().
   Same Q14 trigonometry, half-plane equations, 28.4 stepping and rounding.
   C prepares horizontal commands; the actual bitplane fill is 68000 ASM. */
#include "iris.h"
sIrisSpan gIrisSpans[200];
S16 gIrisX[7],gIrisY[7];
static U16 Wrap(U16 angle){return angle>=1536?angle-1536:angle;}
void Iris_Prepare(S16 h,U16 angle) __attribute__((noinline));
void Iris_Prepare(S16 h,U16 angle)
{
 S32 xb[6],dx[6];S16 ty[6],k,y;U8 kind[6];S16 radius;
 angle%=1536;
 for(k=0;k<6;++k){
  U16 t=Wrap(angle+k*256+128);
  S32 c=Iris_Sine[t+384],sn=Iris_Sine[t],rhs=(S32)h*16384L;
  if(c>256 || c< -256){
   kind[k]=c>0?0:1;
   xb[k]=((rhs+100L*sn)/c)*16L;
   dx[k]=-(sn*16L/c);ty[k]=0;
  }else{
   kind[k]=2;ty[k]=(S16)(100+rhs/sn);xb[k]=sn;dx[k]=0;
  }
 }
 for(y=0;y<200;++y){
  S32 lo=-100000L,hi=100000L;U16 ok=h>2;
  for(k=0;k<6;++k){
   if(kind[k]==0){if(xb[k]<hi)hi=xb[k];}
   else if(kind[k]==1){if(xb[k]>lo)lo=xb[k];}
   else if(xb[k]>0?y>ty[k]:y<ty[k])ok=0;
   xb[k]+=dx[k];
  }
  lo=160+(lo>>4);hi=160+(hi>>4);
  if(lo<0)lo=0;
  if(hi>319)hi=319;
  if(!ok || lo>hi){gIrisSpans[y].left=1;gIrisSpans[y].right=0;}
  else{gIrisSpans[y].left=(S16)lo;gIrisSpans[y].right=(S16)hi;}
 }
 radius=(S16)(((S32)h*37837L)>>15);
 for(k=0;k<7;++k){
  U16 t=Wrap(angle+(k%6)*256);
  gIrisX[k]=160+(S16)(((S32)radius*Iris_Sine[t+384])>>14);
  gIrisY[k]=100+(S16)(((S32)radius*Iris_Sine[t])>>14);
 }
}
void Iris_PrepareEnd(void){}
