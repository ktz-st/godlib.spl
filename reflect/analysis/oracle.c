#include <godlib/platform/platform.h>
#include <godlib/gemdos/gemdos.h>
#include <godlib/ikbd/ikbd.h>
#include <godlib/graphic/reflection.h>
extern void Original_Reflect(sGraphicReflect *);
static U16 guardedSource[16080UL],original[16000UL],ported[16000UL];
#define source (guardedSource+80)
volatile U16 gOracleDone,gOracleFailure,gOracleCase,gOracleTick;
volatile U32 gOracleCompared,gOracleOffset;
static const S16 cases[][3]={{0,199,112},{0,140,140},{0,83,84},
 {50,180,0},{-3,250,-1},{190,199,198},{0,199,199},{0,8,0},{0,199,0},{0,20,0}};
void __attribute__((noinline)) Oracle_Finished(void){gOracleDone=1;}
S16 GodLib_Game_Main(S16 argc,char **argv)
{
    U32 i;U16 c,t; sGraphicReflect a,b;
    (void)argc;(void)argv;GemDos_Super(0);Platform_Init();
    for(i=0;i<16080UL;++i)guardedSource[i]=(U16)((i*31337UL)^(i>>3)^0xa55aUL);
    for(c=0;c<sizeof(cases)/sizeof(cases[0]);++c){
        a.mpSource=b.mpSource=source;a.mpDest=original;b.mpDest=ported;
        a.mSourceY1=b.mSourceY1=cases[c][0];a.mSourceY2=b.mSourceY2=cases[c][1];
        a.mDestY=b.mDestY=cases[c][2];a.mToggle=b.mToggle=a.mPhase=b.mPhase=0;
        for(t=0;t<40;++t){
            gOracleCase=c;gOracleTick=t;
            for(i=0;i<16000UL;++i)original[i]=ported[i]=(U16)(i^0x369c);
            Original_Reflect(&a);Graphic_Reflect(&b);
            for(i=0;i<16000UL;++i)if(original[i]!=ported[i]){
                gOracleOffset=i*2;gOracleFailure=1;goto done;
            }
            if(a.mToggle!=b.mToggle || a.mPhase!=b.mPhase){gOracleFailure=2;goto done;}
            ++gOracleCompared;
        }
    }
 done:Oracle_Finished();
    while(!IKBD_GetKeyStatus(eIKBDSCAN_ESC))IKBD_Update();
    Platform_DeInit();return 0;
}
