#include <godlib/achieve/ach_main.h>
#include <godlib/achieve/ach_god.h>
#include <godlib/encrypt/encrypt.h>
#include <godlib/file/file.h>
#include <godlib/fade/fade.h>
#include <godlib/font8x8/font8x8.h>
#include <godlib/gemdos/gemdos.h>
#include <godlib/ikbd/ikbd.h>
#include <godlib/platform/platform.h>
#include <godlib/screen/screen.h>
#include <stdio.h>
#include <string.h>
extern const char *Achieve_Tasks_GetNewUnLockedTitle(U16 index);
static U32 a[4096],b[4096];static U8 fileBytes[16384];
volatile U16 gAchTestDone,gAchTestPass,gAchTestStage;
#define CHECK(c,n) do{gAchTestStage=n;if(!(c))return 0;}while(0)
static U8 tests(void)
{
 sAchieveUserName names[3]={{{'A',0}},{{'B',0}},{{'C',0}}};S32 hi[3]={100,50,10},lo[3]={10,50,100};
 sAchieveScoreTableDef high={"HIGH",3,eACH_TYPE_U32,eACH_SORT_HI,hi,names},low={"LOW",3,eACH_TYPE_TIME,eACH_SORT_LO,lo,names};
 sAchieveStatDef stat={eACH_TYPE_U32,"ROUNDS"};sAchieveTaskDef task={5,0,"TASK"};sAchieveHeader *h;U16 i;U32 sum,key;S32 size;
 memset(a,0xCC,sizeof(a));memset(b,0xDD,sizeof(b));Achieve_AppInit();Achieve_Create(2,1,9,a,sizeof(a));Achieve_SetGameInfo("RELOCATED GAME",0x12345678UL,0x87654321UL);
 Achieve_Stat_SetStatDef(0,&stat);Achieve_ScoreTable_SetScoreTableDef(0,&high);Achieve_ScoreTable_SetScoreTableDef(1,&low);
 for(i=0;i<9;++i)Achieve_Tasks_SetTaskDef(i,&task);
 Achieve_SetUserInfo("BOB");CHECK(Achieve_Stat_Get(0)==0 && Achieve_Tasks_GetUnLockedCount()==0,1);
 Achieve_Stat_Add(0,2);Achieve_Stat_Max(0,5);Achieve_Stat_Max(0,3);CHECK(Achieve_Stat_Get(0)==5,2);
 CHECK(Achieve_ScoreTable_SetNewScore(0,120)==0 && Achieve_ScoreTable_GetScore(0,1)==100,3);
 CHECK(Achieve_ScoreTable_SetNewScore(1,5)==0 && Achieve_ScoreTable_GetScore(1,1)==10,4);
 CHECK(Achieve_ScoreTable_IsOnTable(0,50) && Achieve_ScoreTable_SetNewScore(0,50)==2,5);
 Achieve_Task_UnLock(0);h=(sAchieveHeader*)a;sum=h->mCheckSum;Achieve_Task_UnLock(8);CHECK(h->mCheckSum!=sum,6);
 CHECK(Achieve_Tasks_GetNewUnLockedCount()==2 && Achieve_Tasks_GetNewUnLockedIndex(1)==8 && !strcmp(Achieve_Tasks_GetNewUnLockedTitle(0),"TASK"),7);
 CHECK(Achieve_Tasks_GetPointsTotal()==45 && Achieve_Tasks_GetPointsUnLocked()==10,8);Achieve_Tasks_ClearNewUnLocked();CHECK(Achieve_Tasks_GetNewUnLockedCount()==0,9);
 Achieve_SetUserInfo("BO");CHECK(Achieve_GetUserCount()==2 && Achieve_Stat_Get(0)==0,10);Achieve_Stat_Update(0,9);
 Achieve_SetUserInfo("BOB2");CHECK(Achieve_GetUserCount()==3 && Achieve_Stat_Get(0)==0,11);
 Achieve_SetUserInfo("BOB");CHECK(Achieve_GetUserCount()==3 && Achieve_Stat_Get(0)==5 && Achieve_Task_IsUnLocked(8),12);
 Achieve_GodLib_AppInit();CHECK(h->mSpecs.mMachine!=0 && h->mSpecs.mRamST!=0,13);
 CHECK(Achieve_Save("STATE.DAT"),14);CHECK(h->mSaveCounter==1 && Achieve_Stat_Get(0)==5,15);
 CHECK(Achieve_Load("STATE.DAT",b,sizeof(b)),16);h=(sAchieveHeader*)b;
 CHECK(!strcmp(h->mGameInfo.mpName,"RELOCATED GAME") && h->mGameInfo.mGameID==0x12345678UL && h->mGameInfo.mBuildID==0x87654321UL && h->mSaveCounter==1,17);
 CHECK((U32)h->mGameInfo.mpName>=(U32)b && (U32)h->mGameInfo.mpName<(U32)(b+4096),18);
 CHECK(Achieve_GetUserCount()==3 && Achieve_Stat_Get(0)==5 && Achieve_Task_IsUnLocked(8) && Achieve_ScoreTable_GetScore(1,0)==5,19);
 Achieve_SetUserInfo("BO");CHECK(Achieve_Stat_Get(0)==9 && !Achieve_Task_IsUnLocked(0),20);
 Achieve_SetUserInfo("NEW");Achieve_Stat_Update(0,7);CHECK(Achieve_GetUserCount()==4,21);
 CHECK(Achieve_Save("STATE.DAT") && Achieve_Load("STATE.DAT",a,sizeof(a)),22);Achieve_SetUserInfo("NEW");CHECK(Achieve_Stat_Get(0)==7,23);
 CHECK(!Achieve_Load("STATE.DAT",b,8) && Achieve_Stat_Get(0)==7,24);
 CHECK(!Achieve_Load("ABSENT.DAT",b,sizeof(b)) && Achieve_Stat_Get(0)==7,25);
 CHECK(!Achieve_Save("Z:\\NO\\BAD.DAT") && Achieve_Stat_Get(0)==7,26);
 File_Save("SHORT.DAT","BAD",3);CHECK(!Achieve_Load("SHORT.DAT",b,sizeof(b)) && Achieve_Stat_Get(0)==7,27);
 size=File_GetSize("STATE.DAT");CHECK(size>0 && size<(S32)sizeof(fileBytes) && File_LoadAt("STATE.DAT",fileBytes),28);
 key=((sAchieveHeader*)fileBytes)->mKey;Endian_FromBigU32(&key);Encrypt_DeScramble(fileBytes,(U32)size,key);
 h=(sAchieveHeader*)fileBytes;h->mGameInfo.mpName=(char*)((U32)size+16);Endian_FromBigU32(&h->mGameInfo.mpName);h->mKey=0;
 Encrypt_Scramble(fileBytes,(U32)size,123);h->mKey=123;Endian_FromBigU32(&h->mKey);File_Save("BAD.DAT",fileBytes,(U32)size);
 CHECK(!Achieve_Load("BAD.DAT",b,sizeof(b)) && Achieve_Stat_Get(0)==7 && !strcmp(Achieve_GetpUserCurrent()->mUserName.mName,"NEW"),29);
 Achieve_Destroy();Achieve_AppDeInit();return 1;
}
S16 GodLib_Game_Main(S16 argc,char **argv)
{
 U16 dirty=2;static U16 pal[16]={0,0x777};char line[40];(void)argc;(void)argv;
 GemDos_Super(0);Platform_Init();Screen_Init(320,200,eGRAPHIC_COLOURMODE_4PLANE,0);Fade_SetPalDirect(pal);
 gAchTestPass=tests();gAchTestDone=1;
 while(!IKBD_GetKeyStatus(eIKBDSCAN_ESC)){Screen_Update();IKBD_Update();if(dirty){Screen_Logic_ClearScreen();sprintf(line,"ACHIEVE %s / CHECK %u",gAchTestPass?"PASS":"FAIL",gAchTestStage);Font8x8_Print(line,Screen_GetpLogic(),0,16);--dirty;}}
 Screen_DeInit();Platform_DeInit();return !gAchTestPass;
}
