#include <godlib/base/base.h>
#include <godlib/gemdos/gemdos.h>
#include "../visual.h"
U16 gPsgLevels[3];
volatile U16 gTestReady,gTestRequest,gTestDone,gTestReset,gTestStyle,gTestPeak;
U16 gTestOld[2][3],gTestBuffers[2][16002];
static void reset(void){U16 p,i,y,w;for(p=0;p<2;++p){for(i=0;i<16002;++i)gTestBuffers[p][i]=(U16)(0xa537U+i*73U);for(y=40;y<170;++y)for(w=8;w<152;++w)gTestBuffers[p][1+y*80+w]=0;for(i=0;i<3;++i)gTestOld[p][i]=0;}PsgDck_Reset();}
S16 GodLib_Game_Main(S16 argc,char **argv){(void)argc;(void)argv;GemDos_Super(0);reset();gTestReady=1;for(;;)if(gTestRequest){U16 n=gTestRequest,p=(n-1)&1,i;gTestRequest=0;if(gTestReset){reset();gTestReset=0;}if(gTestPeak)PsgDck_Update();else for(i=0;i<3;++i)gPsgDckLevels[i]=gPsgLevels[i];gPsgDckDraw[gTestStyle](gTestBuffers[p]+1,gPsgDckLevels,gTestOld[p]);gTestDone=n;}return 0;}
