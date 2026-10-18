/* Original SuperHex bg_render geometry, generated into RAM once at startup.
   C computes span endpoints; Wedges_Span performs the packed bitplane writes. */
#include <godlib/base/base.h>
#include <godlib/memory/memory.h>
#include <godlib/vbl/vbl.h>
extern const S16 Wedges_Sine[1920];
void Wedges_Span(U16 *row,S16 left,S16 right);
U8 *gWedgesCache;
U32 gWedgesBuildVbl;
U16 Wedges_BuildFrames(void)
{
 U16 f;U32 start=Vbl_GetCounter();
 gWedgesCache=Memory_Calloc(256000UL);
 if(!gWedgesCache)return 0;
 for(f=0;f<32;++f){
  U16 angle=f*8+4,par0=((768-angle)>>8)&1;
  S16 cot[3],y,i,j;U16 *row=(U16*)(gWedgesCache+(U32)f*8000UL);
  for(i=0;i<3;++i){
   U16 t=angle+i*256;
   S32 c=Wedges_Sine[t+384],sn=Wedges_Sine[t];
   if(sn> -64 && sn<64)sn=sn<0?-64:64;
   cot[i]=(S16)((c*256L)/sn);
  }
  for(y=0;y<200;++y){
   S16 dy2=2*(y-100)+1,xs[3],left=-1000,right;U16 par=par0;
   for(i=0;i<3;++i){
    S32 x=(320L+(((S32)dy2*cot[i])>>8))>>1;
    if(x< -1000)x=-1000;
    if(x>1000)x=1000;
    xs[i]=(S16)x;
   }
   for(i=0;i<2;++i)for(j=i+1;j<3;++j)if(xs[j]<xs[i]){S16 t=xs[i];xs[i]=xs[j];xs[j]=t;}
   for(i=0;i<=3;++i){
    right=i<3?xs[i]-1:1000;
    if(!par)Wedges_Span(row,left,right);
    left=right+1;par^=1;
   }
   row+=20;
  }
 }
 gWedgesBuildVbl=Vbl_GetCounter()-start;
 return 1;
}
