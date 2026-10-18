/* Adapted from superhex_ste/src/main.c iris_fill().
   Same Q14 trigonometry, half-plane equations, 28.4 stepping and rounding.
   C prepares horizontal commands; the actual bitplane fill is 68000 ASM. */
#include "iris.h"
sIrisSpan gIrisSpans[200];
S16 gIrisX[7],gIrisY[7];
static U16 Wrap(U16 angle){return angle>=1536?angle-1536:angle;}
/* All quotients used here fit signed 16 bits; use native 68000 DIVS/MULS. */
static S32 Divide(S32 value,S16 divisor){__asm__("divs.w %1,%0\n\text.l %0":"+d"(value):"d"(divisor):"cc");return value;}
static S32 Multiply(S16 a,S16 b){S32 value=a;__asm__("muls.w %1,%0":"+d"(value):"d"(b):"cc");return value;}
void Iris_Prepare(S16 h,U16 angle) __attribute__((noinline));
void Iris_Prepare(S16 h,U16 angle)
{
 sIrisRun runs[6];S32 start[6],step[6];S16 k,r=0,l=3,first=0,last=199,y,ri=0;S16 radius;
 angle%=1536;
 for(k=0;k<6;++k){start[k]=k<3?100000L:-100000L;step[k]=0;}
 for(k=0;k<6;++k){
  U16 t=Wrap(angle+k*256+128);S16 index;
  S16 c=Iris_Sine[t+384],sn=Iris_Sine[t];S32 rhs=(S32)h*16384L;
  if(c>256 || c< -256){
   index=c>0?r++:l++;
   start[index]=Divide(rhs+Multiply(100,sn),c)*16L;
   step[index]=-Divide((S32)sn*16,c);
  }else{
   S16 y=(S16)(100+Divide(rhs,sn));
   if(sn>0){if(y<last)last=y;}else if(y>first)first=y;
  }
 }
 if(first<0)first=0;
 if(first>200)first=200;
 if(last>199)last=199;
 if(last< -1)last=-1;
 if(h<=2)last=-1;
 for(y=first;y<=last;){
  S32 value[6];S16 left=3,right=0,next=last+1,j;
  for(k=0;k<6;++k)value[k]=start[k]+Multiply((S16)step[k],y);
  for(k=1;k<3;++k)if(value[k]<value[right])right=k;
  for(k=4;k<6;++k)if(value[k]>value[left])left=k;
  for(k=0;k<6;++k){
   S32 slope,delta,n;
   j=k<3?right:left;
   slope=k<3?step[j]-step[k]:step[k]-step[j];
   if(slope<=0)continue;
   delta=k<3?value[k]-value[j]:value[j]-value[k];
   if(delta>=Multiply((S16)slope,next-y))continue;
   n=Divide(delta,(S16)slope)+1;
   if(n<next-y)next=y+(S16)n;
  }
  runs[ri].xL=value[left]*4096L;runs[ri].xR=value[right]*4096L;
  runs[ri].dxL=step[left]*4096L;runs[ri].dxR=step[right]*4096L;
  {
   S32 lastL=value[left]+Multiply((S16)step[left],next-y-1);
   S32 lastR=value[right]+Multiply((S16)step[right],next-y-1);
   U16 count=next-y;
   if(value[left]-value[right]>=16 && lastL-lastR>=16)count=(U16)(-(S16)count);
   else if(value[left]<= -2560 && lastL<= -2560 && value[right]>=2544 && lastR>=2544)count|=0x4000;
   runs[ri++].count=count;y=next;
  }
 }
 runs[ri].count=0;
 Iris_Scan(gIrisSpans,runs,first,last);
 radius=(S16)(((S32)h*37837L)>>15);
 for(k=0;k<7;++k){
  U16 t=Wrap(angle+(k%6)*256);
  gIrisX[k]=160+(S16)(Multiply(radius,Iris_Sine[t+384])>>14);
  gIrisY[k]=100+(S16)(Multiply(radius,Iris_Sine[t])>>14);
 }
}
void Iris_PrepareEnd(void){}
