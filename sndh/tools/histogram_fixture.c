#include <godlib/base/base.h>
#include <godlib/gemdos/gemdos.h>
extern U8 gPsgHistogram[16];
extern void PsgHistogram_Update(void),PsgHistogram_Reset(void),PsgHistogram_Draw(void *,const U8 *,U8 *);
volatile U8 gPsgRegisters[12],gTestInput[3];
volatile U16 gTestReady,gTestRequest,gTestDone,gTestReset;
U16 gTestBuffers[2][16002];
U8 gTestOld[2][16];
S16 GodLib_Game_Main(S16 argc,char **argv)
{
 U16 page,i,y,col;(void)argc;(void)argv;GemDos_Super(0);
 for(page=0;page<2;++page){
  for(i=0;i<16002;++i)gTestBuffers[page][i]=(U16)(i*73U+0xa537U);
  for(y=112;y<144;++y)for(col=0;col<16;++col)gTestBuffers[page][1+y*80+(col+2)*4]=0;
 }
 PsgHistogram_Reset();gTestReady=1;
 for(;;)if(gTestRequest){
  U16 request=gTestRequest;gTestRequest=0;page=(request-1)&1;
  gPsgRegisters[8]=gTestInput[0];gPsgRegisters[9]=gTestInput[1];gPsgRegisters[10]=gTestInput[2];
  if(gTestReset){PsgHistogram_Reset();gTestReset=0;}
  PsgHistogram_Update();PsgHistogram_Draw(gTestBuffers[page]+1,gPsgHistogram,gTestOld[page]);gTestDone=request;
 }
 return 0;
}
