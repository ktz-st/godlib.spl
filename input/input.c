/* Kernel owns frame scheduling and record/replay; gameplay consumes one sInput. */
#include <godlib/kernel/kernel.h>
#include <godlib/ikbd/ikbd.h>
#include <godlib/font8x8/font8x8.h>
#include <godlib/platform/platform.h>
#include <godlib/screen/screen.h>
#include <godlib/fade/fade.h>
#include <godlib/gemdos/gemdos.h>
#include <godlib/file/file.h>
#include <godlib/vbl/vbl.h>
#include <stdio.h>
#include <string.h>
#define CAPACITY 32768UL
#define RECORD_FILE "INPUTS.KIP"
static S16 x=154,y=88,endX,endY;
static U16 fires,endFires,colour,endColour,wasReplay,wasRecord,reference;
static U32 digest=0x12345678UL,endDigest;
static sInput visible;
static char message[40]="R: RECORD A ROUTE / P: REPLAY";
static U16 pal[16]={0x001,0x012,0x123,0x235,0x346,0x024,0x777,0x57a,0x09a,0x78e,0x2fd,0x3ac,0xabc,0xf80,0xf90,0xffe};
volatile U16 gInReady,gInExited,gInTaskInit,gInTaskDeInit,gInMode,gInFires,gInMatch,gInChecks,gInSaveOK,gInLoadOK,gInKeys,gInJoy,gInHeld,gInHit,gInUnhit;
volatile S16 gInX,gInY;
volatile U32 gInFrames,gInRecordFrames,gInBytes,gInFrame,gInDigest,gInEndDigest,gInCallsAfterExit;
static void reset(void){x=154;y=88;fires=0;colour=0;digest=0x12345678UL;}
static void endpoint(void){endX=x;endY=y;endFires=fires;endColour=colour;endDigest=digest;reference=1;gInEndDigest=endDigest;}
static void apply(const sInput *in)
{
 S16 dx=(in->mKeyStatus[eINPUTKEY_RIGHT]&1?2:0)-(in->mKeyStatus[eINPUTKEY_LEFT]&1?2:0);
 S16 dy=(in->mKeyStatus[eINPUTKEY_DOWN]&1?2:0)-(in->mKeyStatus[eINPUTKEY_UP]&1?2:0);U16 i,bits=0;
 x+=dx;y+=dy;if(x<12)x=12;if(x>296)x=296;if(y<52)y=52;if(y>124)y=124;
 if(in->mKeyStatus[eINPUTKEY_FIREA]&eINPUTKEYSTATUS_HIT){++fires;colour=(colour+1)%3;}
 for(i=0;i<eINPUTKEY_LIMIT;++i)bits=(U16)((bits<<1)^in->mKeyStatus[i]);
 digest=((digest<<5)|(digest>>27))^(U32)(U16)x^((U32)(U16)y<<16)^fires^bits;
}
static void box(S16 bx,S16 by,S16 w,S16 h,U16 c)
{sGraphicCanvas *canvas=Screen_GetpLogicGraphic();sGraphicRect r={bx,by,w,h};canvas->mpClipFuncs->DrawBox(canvas,&r,c);}
static void text(const char *s,U16 tx,U16 ty,U16 c){Font8x8_PrintColourCanvas(s,Screen_GetpLogicGraphic(),tx,ty,c);}
static U16 mask(const sInput *in,U8 flag){U16 i,b=0;for(i=0;i<eINPUTKEY_LIMIT;++i)if(in->mKeyStatus[i]&flag)b|=(1<<i);return b;}
static void draw(void)
{
 char line[40],held[10],hit[10],unhit[10];U16 i;const char *mode=Kernel_GetInputMode()==eKERNEL_INPUT_SAVING?"RECORD":Kernel_GetInputMode()==eKERNEL_INPUT_LOADING?"REPLAY":"LIVE";
 sGraphicCanvas *c=Screen_GetpLogicGraphic();c->mpFuncs->ClearScreen(c);
 box(8,6,304,34,1);text("INPUT / KERNEL",16,10,15);
 snprintf(line,sizeof(line),"%-6s %5lu FRAMES %5lu BYTES",mode,Kernel_GetInputFrameCount(),Kernel_GetInputBytes());text(line,16,26,10);
 box(8,48,304,92,3);box(9,49,302,90,0);
 for(i=40;i<304;i+=32)box(i,50,1,88,1);
 for(i=64;i<138;i+=16)box(10,i,300,1,1);
 if(reference){box(endX-1,endY-1,14,14,4);box(endX,endY,12,12,0);}
 box(x,y,12,12,(U16)(10+colour));box(x+3,y+3,6,6,(visible.mKeyStatus[eINPUTKEY_FIREA]&1)?15:0);
 snprintf(line,sizeof(line),"X %3d Y %3d  FIRE %u",x,y,fires);text(line,16,144,15);
 Input_BuildHeldString(&visible,held);Input_BuildHitString(&visible,hit);Input_BuildUnHitString(&visible,unhit);
 snprintf(line,sizeof(line),"H %s + %s - %s",held,hit,unhit);text(line,8,156,10);
 text(message,8,170,15);text("ARROWS/JOY1 SPACE/FIRE  R REC P PLAY",8,182,10);text("S SAVE L LOAD  C RESET  ESC/F10 EXIT",8,192,10);
}
static void init(void){++gInTaskInit;reset();gInReady=1;}
static void deinit(void){++gInTaskDeInit;}
static U16 update(sInput *in)
{
 U8 sc;U16 replay=(Kernel_GetInputMode()==eKERNEL_INPUT_LOADING),record=(Kernel_GetInputMode()==eKERNEL_INPUT_SAVING),skip=0;
 if(wasReplay&&!replay){
  if(reference){gInMatch=(x==endX&&y==endY&&fires==endFires&&colour==endColour&&digest==endDigest);++gInChecks;strcpy(message,gInMatch?"REPLAY MATCH / SAME ROUTE AND EVENTS":"REPLAY MISMATCH");}
  else strcpy(message,"REPLAY FINISHED / FILE HAS NO STATE");
  skip=1;
 }
 if(wasRecord&&!record){endpoint();strcpy(message,"BUFFER FULL / RECORDING STOPPED");skip=1;}
 visible=*in;if(!skip)apply(in);
 /* Recorder controls are live IKBD events, never replayed game actions.
  * Process after gameplay: the current recorded frame is applied exactly once. */
 while(IKBD_GetKbdBytesWaiting()){
  sc=IKBD_PopKbdByte();if(sc&0x80)continue;
  if(sc==eIKBDSCAN_ESC){Kernel_InputStop();Kernel_RequestShutdown();}
  else if(sc==eIKBDSCAN_R){
   if(record){Kernel_InputStop();endpoint();strcpy(message,"RECORDING STOPPED / P TO REPLAY");}
   else if(Kernel_InputRecordBegin(CAPACITY)){reset();reference=0;gInMatch=0;strcpy(message,"RECORDING / R STOP / P REPLAY");}
  }else if(sc==eIKBDSCAN_P){
   if(replay){Kernel_InputStop();strcpy(message,"REPLAY ABORTED / LIVE INPUT");}
   else {if(record)endpoint();if(Kernel_InputReplayBegin()){reset();gInMatch=0;strcpy(message,"REPLAY / LIVE DIRECTIONS IGNORED");}}
  }else if(sc==eIKBDSCAN_S && !replay){
   if(record){Kernel_InputStop();endpoint();}
   gInSaveOK=Kernel_InputBufferWrite(RECORD_FILE);strcpy(message,gInSaveOK?"SAVED INPUTS.KIP":"SAVE FAILED / RECORD SOMETHING");
  }else if(sc==eIKBDSCAN_L){
   gInLoadOK=Kernel_InputBufferRead(RECORD_FILE);if(gInLoadOK){reset();reference=0;strcpy(message,"LOADED INPUTS.KIP / REPLAY");}else strcpy(message,"LOAD FAILED / RECORDING KEPT");
  }else if(sc==eIKBDSCAN_C&&!replay&&!record){reset();strcpy(message,"LIVE SCENE RESET");}
 }
 if(in->mKeyStatus[eINPUTKEY_QUIT]&eINPUTKEYSTATUS_HIT){Kernel_InputStop();Kernel_RequestShutdown();}
 wasReplay=(Kernel_GetInputMode()==eKERNEL_INPUT_LOADING);wasRecord=(Kernel_GetInputMode()==eKERNEL_INPUT_SAVING);
 gInMode=Kernel_GetInputMode();gInX=x;gInY=y;gInFires=fires;gInRecordFrames=Kernel_GetInputFrameCount();gInBytes=Kernel_GetInputBytes();gInFrame=Kernel_GetInputFrame();gInDigest=digest;++gInFrames;
 gInKeys=IKBD_GetKeyStatus(eIKBDSCAN_RIGHTARROW)!=0;gInJoy=IKBD_GetJoy1Packet();gInHeld=mask(in,1);gInHit=mask(in,2);gInUnhit=mask(in,4);
 draw();return 7;
}
static sKernelTask tasks[]={{7,0,init,deinit,update}};
S16 GodLib_Game_Main(S16 argc,char **argv)
{
 sGemDosDTA *dta;U16 calls;(void)argc;(void)argv;
 GemDos_Super(0);Platform_Init();Screen_Init(320,200,eGRAPHIC_COLOURMODE_4PLANE,0);Fade_SetPalDirect(pal);
 dta=File_GetDTA();calls=Vbl_GetpVbl()->mCallCount;Kernel_Init(tasks,1,0,0,0);Kernel_Main();Kernel_DeInit();
 gInCallsAfterExit=(U32)(Vbl_GetpVbl()->mCallCount-calls);gInExited=(File_GetDTA()==dta&&gInTaskInit==1&&gInTaskDeInit==1&&gInCallsAfterExit==0);
 Screen_DeInit();Platform_DeInit();return gInExited?0:1;
}
