/* Achieve owns the profiles, score table, stats, awards and disk format.
 * This compact UI uses GodLib's existing canvas/font/sprite kernels. */
#include <godlib/achieve/ach_main.h>
#include <godlib/achieve/ach_god.h>
#include <godlib/fade/fade.h>
#include <godlib/file/file.h>
#include <godlib/font/font.h>
#include <godlib/gemdos/gemdos.h>
#include <godlib/ikbd/ikbd.h>
#include <godlib/memory/memory.h>
#include <godlib/platform/platform.h>
#include <godlib/screen/screen.h>
#include <stdio.h>
#include <string.h>
#define ARENA_SIZE 16384UL
#define SAVE_NAME "ACHDEMO.DAT"
extern U8 Ach_Font[],Ach_Active[];
static U32 arenas[2][ARENA_SIZE/4];
static U16 arena,dirty=2,tab,editing;
static S32 score=750;
static char name[16]="ATARI",edit[16],message[40]="N: NEW PLAYER   ENTER: ADD ROUND";
static U16 palette[16]={0x001,0x012,0x123,0x235,0x346,0x024,0x777,0x57a,0x09a,0x78e,0x2fd,0x3ac,0xabc,0xf80,0xf90,0xffe};
static sAchieveUserName seedNames[5]={{{'G','O','D','S',0}},{{'S','T','E',0}},{{'S','T',0}},{{'P','U','R','E','C',0}},{{'G','C','C',0}}};
static S32 seedValues[5]={2000,1500,1000,500,250};
volatile U16 gAchReady,gAchExited,gAchEditing,gAchTab,gAchUsers,gAchUnlocked,gAchNew,gAchPoints,gAchSaveOK,gAchLoadOK,gAchSaveCount,gAchLoadCount,gAchRoundCount;
volatile U32 gAchGames,gAchBest,gAchTop,gAchArenaAddress;
char gAchPlayer[16];
void AchExample_Frame(void)__attribute__((noinline));void AchExample_Frame(void){__asm__ volatile("nop");}
static void defaults(void)
{
 sAchieveScoreTableDef table={"TOP FIVE",5,eACH_TYPE_U32,eACH_SORT_HI,seedValues,seedNames};
 sAchieveStatDef games={eACH_TYPE_U32,"ROUNDS PLAYED"},best={eACH_TYPE_U32,"BEST SCORE"};
 sAchieveTaskDef tasks[3]={{10,0,"FIRST ROUND"},{25,0,"SCORE AT LEAST 1000"},{50,0,"PLAY THREE ROUNDS"}};U16 i;
 Achieve_Create(1,2,3,arenas[arena],ARENA_SIZE);Achieve_SetGameInfo("ACHIEVE DEMO",0x41434844UL,1);
 Achieve_Stat_SetStatDef(0,&games);Achieve_Stat_SetStatDef(1,&best);Achieve_ScoreTable_SetScoreTableDef(0,&table);
 for(i=0;i<3;++i)Achieve_Tasks_SetTaskDef(i,&tasks[i]);
 Achieve_SetUserInfo("ATARI");Achieve_GodLib_AppInit();
}
static void snapshot(void)
{
 gAchEditing=editing;gAchTab=tab;gAchUsers=Achieve_GetUserCount();gAchGames=Achieve_Stat_Get(0);gAchBest=Achieve_Stat_Get(1);
 gAchUnlocked=Achieve_Tasks_GetUnLockedCount();gAchNew=Achieve_Tasks_GetNewUnLockedCount();gAchPoints=(U16)Achieve_Tasks_GetPointsUnLocked();
 gAchTop=(U32)Achieve_ScoreTable_GetScore(0,0);gAchArenaAddress=(U32)arenas[arena];strcpy(gAchPlayer,name);
}
static void text(sGraphicCanvas *c,const char *s,S16 x,S16 y,U16 active)
{sGraphicPos p={x,y};c->mpClipFuncs->FontPrint(c,&p,(sFont*)(active?Ach_Active:Ach_Font),s);}
static void box(sGraphicCanvas *c,S16 x,S16 y,S16 w,S16 h,U16 colour)
{sGraphicRect r={x,y,w,h};c->mpClipFuncs->DrawBox(c,&r,colour);}
static void draw(void)
{
 sGraphicCanvas *c=Screen_GetpLogicGraphic();char line[48];U16 i;
 c->mpFuncs->ClearScreen(c);box(c,8,8,304,188,3);box(c,9,9,302,186,0);box(c,16,46,288,111,1);
 text(c,"ACHIEVE / PLAYER PROFILE",24,16,1);snprintf(line,sizeof(line),"PLAYER %-15s USERS %u",name,gAchUsers);text(c,line,24,31,0);
 if(!tab){
  text(c,"TOP FIVE",24,53,1);
  for(i=0;i<5;++i){snprintf(line,sizeof(line),"%u %-15s %7ld",i+1,Achieve_ScoreTable_GetpName(0,i),Achieve_ScoreTable_GetScore(0,i));text(c,line,24,(S16)(68+i*12),0);}
  snprintf(line,sizeof(line),"ROUND SCORE %5ld    < / >",score);text(c,line,24,135,1);
 }else{
  for(i=0;i<3;++i){snprintf(line,sizeof(line),"[%c] %-19s %2lu",Achieve_Task_IsUnLocked(i)?'X':' ',Achieve_Tasks_GetpTitle(i),Achieve_Task_GetPoints(i));text(c,line,20,(S16)(54+i*14),Achieve_Task_IsUnLocked(i)!=0);}
  snprintf(line,sizeof(line),"ROUNDS %lu  BEST %lu",gAchGames,gAchBest);text(c,line,24,102,0);
  snprintf(line,sizeof(line),"AWARDS %u/3  POINTS %u/85",gAchUnlocked,gAchPoints);text(c,line,24,118,1);
  snprintf(line,sizeof(line),"NEW AWARDS %u   A: ACKNOWLEDGE",gAchNew);text(c,line,24,140,0);
 }
 text(c,message,16,162,1);text(c,"TAB: VIEW  N: PLAYER  S: SAVE",16,176,0);text(c,"L: LOAD  ENTER: ROUND  ESC: EXIT",16,186,0);
 if(editing){box(c,32,66,256,64,10);box(c,33,67,254,62,2);text(c,"PLAYER NAME / 15 CHARACTERS",40,76,1);snprintf(line,sizeof(line),"%s_",edit);text(c,line,40,94,1);text(c,"ENTER: OK   ESC: CANCEL",40,113,0);}
}
static void round_add(void)
{
 U16 count;S16 place;
 Achieve_Stat_Add(0,1);Achieve_Stat_Max(1,(U32)score);place=Achieve_ScoreTable_SetNewScore(0,score);
 Achieve_Task_UnLock(0);if(score>=1000)Achieve_Task_UnLock(1);if(Achieve_Stat_Get(0)>=3)Achieve_Task_UnLock(2);
 count=Achieve_Tasks_GetNewUnLockedCount();++gAchRoundCount;
 snprintf(message,sizeof(message),"ROUND ADDED / RANK %u / NEW %u",place<5?(U16)(place+1):0,count);
}
static void load(void)
{
 U16 next=(U16)(arena^1);
 gAchLoadOK=Achieve_Load(SAVE_NAME,arenas[next],ARENA_SIZE);++gAchLoadCount;
 if(gAchLoadOK){arena=next;strcpy(name,Achieve_GetUserName(0));Achieve_SetUserInfo(name);strcpy(message,"PROFILES LOADED / OTHER RAM BUFFER");}
 else strcpy(message,"LOAD FAILED / CURRENT DATA KEPT");
}
S16 GodLib_Game_Main(S16 argc,char **argv)
{
 U16 quit=0;U8 scan,ch;U16 len;(void)argc;(void)argv;
 GemDos_Super(0);Platform_Init();Screen_Init(320,200,eGRAPHIC_COLOURMODE_4PLANE,0);Fade_SetPalDirect(palette);
 Font_Relocate((sFont*)Ach_Font);Font_Relocate((sFont*)Ach_Active);Achieve_AppInit();defaults();
 if(File_Exists(SAVE_NAME))load();
 snapshot();gAchReady=1;
 while(!quit){Screen_Update();IKBD_Update();
  while(IKBD_GetKbdBytesWaiting()){
   scan=IKBD_PopKbdByte();if(scan&0x80)continue;dirty=2;
   if(editing){
    len=(U16)strlen(edit);
    if(scan==eIKBDSCAN_ESC)editing=0;
    else if(scan==eIKBDSCAN_BACKSPACE){if(len)edit[len-1]=0;}
    else if(scan==eIKBDSCAN_RETURN){if(len){
     if(Achieve_GetUserCount()<8 || !strcmp(edit,name)){Achieve_SetUserInfo(edit);strcpy(name,edit);strcpy(message,"PLAYER SELECTED / INDEPENDENT STATS");editing=0;}
     else {U16 i;for(i=0;i<Achieve_GetUserCount();++i)if(!strcmp(edit,Achieve_GetUserName(i)))break;if(i<Achieve_GetUserCount()){Achieve_SetUserInfo(edit);strcpy(name,edit);editing=0;}else strcpy(message,"DEMO LIMIT: 8 PLAYERS");}
    }}else {ch=IKBD_ConvertScancodeAsciiCaps(scan);if(ch>=32 && ch<127 && len<15){edit[len]=(char)ch;edit[len+1]=0;}}
    continue;
   }
   switch(scan){
    case eIKBDSCAN_ESC:quit=1;break;
    case eIKBDSCAN_TAB:tab^=1;break;
    case eIKBDSCAN_N:edit[0]=0;editing=1;break;
    case eIKBDSCAN_LEFTARROW:if(score>=250)score-=250;break;
    case eIKBDSCAN_RIGHTARROW:if(score<999000)score+=250;break;
    case eIKBDSCAN_RETURN:round_add();break;
    case eIKBDSCAN_A:Achieve_Tasks_ClearNewUnLocked();strcpy(message,"NEW AWARDS ACKNOWLEDGED");break;
    case eIKBDSCAN_S:gAchSaveOK=Achieve_Save(SAVE_NAME);++gAchSaveCount;strcpy(message,gAchSaveOK?"SAVED TO ACHDEMO.DAT":"SAVE FAILED");break;
    case eIKBDSCAN_L:load();break;
   }
  }
  snapshot();if(dirty){draw();--dirty;}AchExample_Frame();
 }
 Achieve_Destroy();Achieve_AppDeInit();Screen_DeInit();Platform_DeInit();gAchExited=1;return 0;
}
