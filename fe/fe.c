/* Native FE runtime: FEBUILD data owns layout, links, selectors and transitions. */
#include <godlib/fe/fed.h>
#include <godlib/fe/r_fed.h>
#include <godlib/asset/context.h>
#include <godlib/audio/amixer.h>
#include <godlib/fade/fade.h>
#include <godlib/font8x8/font8x8.h>
#include <godlib/gemdos/gemdos.h>
#include <godlib/ikbd/ikbd.h>
#include <godlib/input/input.h>
#include <godlib/memory/memory.h>
#include <godlib/platform/platform.h>
#include <godlib/screen/screen.h>
#include <godlib/system/system.h>
#include <stdio.h>
#include <string.h>

extern U8 Fe_Menu[],Fe_MenuEnd[],Fe_Normal[],Fe_Active[],Fe_Title[],Fe_Cursor[],Fe_Main[],Fe_Options[],Fe_Chime[],Fe_ChimeEnd[];
extern U16 gFedMode;
static sHashTree tree;
static sHashTreeVar vars[3];
static sContext context;
static sInput keys,joy,input;
static sAudioDmaSound chime;
static sFedHeader *menu;
static char status[40];
volatile U16 gFeReady,gFeExited,gFePage,gFeSelection,gFeMode,gFeRoundtrip,gFeCalls,gFeStarts,gFeSounds,gFeVolumeGain,gFeError;
volatile S32 gFeDifficulty,gFeVolume,gFeContextRefs;
volatile U32 gFeFrames,gFeCleanupVars;
void FeExample_Frame(void) __attribute__((noinline));void FeExample_Frame(void){__asm__ volatile("nop");}
static void variable(U16 i,const char *name,S32 value)
{HashTree_Var_Init(&vars[i],&tree,name,4,&value);HashTree_VarWrite(&vars[i],&value);}
static void *asset(const char *name)
{
 if(!strcmp(name,"NORMAL.BFB"))return Fe_Normal;
 if(!strcmp(name,"ACTIVE.BFB"))return Fe_Active;
 if(!strcmp(name,"TITLE.BFB"))return Fe_Title;
 if(!strcmp(name,"MAIN.PI1"))return Fe_Main;
 if(!strcmp(name,"OPTIONS.PI1"))return Fe_Options;
 if(!strcmp(name,"CURSOR.BSB"))return Fe_Cursor;
 return 0;
}
static void snapshot(void)
{
 sFedPage *page=Fed_GetpActivePage();
 HashTree_VarRead(&vars[0],(void*)&gFeDifficulty,4);HashTree_VarRead(&vars[1],(void*)&gFeVolume,4);
 gFePage=(U16)(page-menu->mpPages);gFeSelection=page->mpControlList->mControlIndex;gFeMode=gFedMode;
}
S16 GodLib_Game_Main(S16 argc,char **argv)
{
 U16 i,quit=0,audio=0;S32 action,zero=0;U32 size=(U32)(Fe_MenuEnd-Fe_Menu);U8 *copy;const char *difficulties[]={"EASY","MEDIUM","HARD"};
 (void)argc;(void)argv;GemDos_Super(0);Platform_Init();Screen_Init(320,200,eGRAPHIC_COLOURMODE_4PLANE,0);
 menu=(sFedHeader*)Fe_Menu;copy=mMEMCALLOC(size);
 if(!copy){gFeError=1;goto end;}
 Memory_Copy(size,Fe_Menu,copy);Fed_Relocate(menu);Fed_Delocate(menu);gFeRoundtrip=!memcmp(copy,Fe_Menu,size);mMEMFREE(copy);
 if(!gFeRoundtrip){gFeError=2;goto end;}
 Fed_Relocate(menu);Font_Relocate((sFont*)Fe_Normal);Font_Relocate((sFont*)Fe_Active);Font_Relocate((sFont*)Fe_Title);Sprite_BlockRelocate((sSpriteBlock*)Fe_Cursor);
 HashTree_Init(&tree);variable(0,"FE/DIFFICULTY",1);variable(1,"FE/VOLUME",70);variable(2,"FE/ACTION",0);
 Context_Init(&context,"FE_DEMO");Fed_SetpHashTree(&tree);Fed_Init(menu);
 for(i=0;i<menu->mAssetCount;++i){menu->mpAssets[i].mpData=asset(menu->mpAssets[i].mpFileName);if(!menu->mpAssets[i].mpData)gFeError=3;}
 RenderFed_Init();Input_Init(&keys);keys.mScanCodes[eINPUTKEY_FIREA]=eIKBDSCAN_RETURN;keys.mScanCodes[eINPUTKEY_FIREB]=eIKBDSCAN_SPACE;Input_Init(&joy);joy.mInputType=eINPUTTYPE_JOY1;
 if(System_GetMCH()!=MCH_ST){AudioMixer_Init();AudioMixer_SetFrequency(eAUDIO_FREQ_12);AudioMixer_Enable();audio=1;}
 chime.mpSound=Fe_Chime;chime.mLength=Fe_ChimeEnd-Fe_Chime;chime.mFreq=eAUDIO_FREQ_12;chime.mBits=eAUDIO_BITS_8;chime.mStereoFlag=0;chime.mLoopingFlag=0;
 Fade_SetPalDirect((U16*)Fe_Main+1);Fed_Begin(menu,"MAIN");gFeReady=1;
 while(!quit && !gFeError){
  Screen_Update();IKBD_Update();Input_Update(&keys);Input_Update(&joy);input=keys;Input_Combine(&input,&keys,&joy);
  input.mKeyStatus[eINPUTKEY_FIREA]|=input.mKeyStatus[eINPUTKEY_FIREB];
  if(input.mKeyStatus[eINPUTKEY_QUIT]&eINPUTKEYSTATUS_HIT)quit=1;
  if(Fed_Update(&input)){
   HashTree_VarRead(&vars[2],&action,4);snapshot();++gFeCalls;
   if(action==2)quit=1;
   else if(action==1){
    ++gFeStarts;snprintf(status,sizeof(status),"START / %s / VOL %ld",difficulties[gFeDifficulty],gFeVolume);
    menu->mpPages[0].mpTitle->mpString=status;menu->mpPages[0].mRedrawFlag=2;
   }else if(action==3){++gFeSounds;gFeVolumeGain=(U16)(gFeVolume*255L/100L);if(audio)AudioMixer_PlayVoice(0,&chime,(U8)gFeVolumeGain,eAMIXER_PAN_CENTRE);}
   HashTree_VarWrite(&vars[2],&zero);
  }
  RenderFed_Update(Screen_GetpLogicGraphic(),Screen_GetpBackGraphic());snapshot();++gFeFrames;FeExample_Frame();
 }
 if(audio)AudioMixer_DeInit();
 RenderFed_DeInit();Fed_DeInit(menu);gFeContextRefs=context.mRefCount;Context_DeInit(&context);Fed_SetpHashTree(0);
 for(i=0;i<3;++i)HashTree_Var_DeInit(&vars[i],&tree);
 {sHashTreeVar *v;for(v=tree.mpVars;v;v=v->mpVarNext)++gFeCleanupVars;}HashTree_DeInit(&tree);
end:
 Screen_DeInit();Platform_DeInit();gFeExited=1;return gFeError;
}
