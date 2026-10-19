#include <godlib/kernel/kernel.h>
#include <godlib/ikbd/ikbd.h>
#include <godlib/platform/platform.h>
#include <godlib/screen/screen.h>
#include <godlib/fade/fade.h>
#include <godlib/gemdos/gemdos.h>
#include <godlib/font8x8/font8x8.h>
#include <godlib/file/file.h>
#include <godlib/memory/memory.h>
#include <godlib/vbl/vbl.h>
#include <string.h>
#include <stdio.h>
extern sIKBD gIKBD;
extern void Kernel_InputBufferSet(const sInput *in);
extern void Kernel_InputBufferGet(sInput *in);
volatile U16 gInputTestDone,gInputTestPass,gInputTestStage;
#define CHECK(expr,id) do{gInputTestStage=id;if(!(expr))return 0;}while(0)
static void noop(void){}
static U16 idle(sInput *in){(void)in;return 7;}
static sKernelTask task={7,0,noop,noop,idle};
static U8 file[256];
static U16 tests(void)
{
 sInput src[2],dst,a,b,c,out;U32 bytes,frames;U16 i;U8 *p=(U8*)&b;sGemDosDTA *oldDta=File_GetDTA();U16 calls=Vbl_GetpVbl()->mCallCount;
 Input_CombinedInit(&dst,src,2);src[0].mInputType=src[1].mInputType=eINPUTTYPE_AI;
 src[0].mKeyStatus[eINPUTKEY_RIGHT]=3;src[1].mKeyStatus[eINPUTKEY_RIGHT]=4;
 Input_CombinedUpdate(&dst,src,2);CHECK(dst.mKeyStatus[eINPUTKEY_RIGHT]==3,1);
 src[1].mKeyStatus[eINPUTKEY_RIGHT]=1;Input_CombinedUpdate(&dst,src,2);CHECK(dst.mKeyStatus[eINPUTKEY_RIGHT]==1,2);
 src[0].mKeyStatus[eINPUTKEY_RIGHT]=4;Input_CombinedUpdate(&dst,src,2);CHECK(dst.mKeyStatus[eINPUTKEY_RIGHT]==1,3);
 src[1].mKeyStatus[eINPUTKEY_RIGHT]=0;Input_CombinedUpdate(&dst,src,2);CHECK(dst.mKeyStatus[eINPUTKEY_RIGHT]==4,4);
 Input_CombinedUpdate(&dst,src,2);CHECK(dst.mKeyStatus[eINPUTKEY_RIGHT]==0,5);
 Input_Init(&dst);gIKBD.mKbdPressTable[eIKBDSCAN_SPACE]=1;Input_Update(&dst);CHECK(dst.mKeyStatus[eINPUTKEY_FIREA]==3,6);
 gIKBD.mKbdPressTable[eIKBDSCAN_SPACE]=0;Input_Update(&dst);CHECK(dst.mKeyStatus[eINPUTKEY_FIREA]==4,7);
 gIKBD.mKbdPressTable[eIKBDSCAN_SPACE]=1;Input_Update(&dst);CHECK(dst.mKeyStatus[eINPUTKEY_FIREA]==3,8);
 gIKBD.mKbdPressTable[eIKBDSCAN_SPACE]=0;
 Kernel_Init(&task,1,0,0,0);Memory_Clear(sizeof(a),&a);Memory_Clear(sizeof(c),&c);
 CHECK(!Kernel_InputReplayBegin() && !Kernel_InputRecordBegin(sizeof(sInput)-1),9);
 CHECK(Kernel_InputRecordBegin(256),10);
 a.mKeyStatus[eINPUTKEY_RIGHT]=3;Kernel_InputBufferSet(&a);Kernel_InputBufferSet(&a);
 for(i=0;i<sizeof(b);++i)p[i]=(U8)(i+1);
 Kernel_InputBufferSet(&b);Kernel_InputBufferSet(&c);
 CHECK(Kernel_GetInputFrameCount()==4 && Kernel_GetInputBytes()==sizeof(sInput)*5UL+1,11);
 CHECK(Kernel_InputBufferWrite("TEST.KIP"),12);bytes=Kernel_GetInputBytes();
 CHECK(Kernel_InputReplayBegin(),13);Kernel_InputBufferGet(&out);CHECK(!memcmp(&out,&a,sizeof(a)),14);
 Kernel_InputBufferGet(&out);CHECK(!memcmp(&out,&a,sizeof(a)),15);
 Kernel_InputBufferGet(&out);CHECK(!memcmp(&out,&b,sizeof(b)),16);
 Kernel_InputBufferGet(&out);CHECK(!memcmp(&out,&c,sizeof(c)) && Kernel_GetInputFrame()==4,17);
 out=a;Kernel_InputBufferGet(&out);CHECK(Kernel_GetInputMode()==eKERNEL_INPUT_NORMAL && !memcmp(&out,&c,sizeof(c)),18);
 CHECK(Kernel_InputBufferRead("TEST.KIP") && Kernel_GetInputFrameCount()==4 && Kernel_GetInputBytes()==bytes,19);
 Kernel_InputBufferGet(&out);CHECK(!memcmp(&out,&a,sizeof(a)),20);
 frames=Kernel_GetInputFrameCount();File_Save("SHORT.KIP",file,sizeof(sInput)-1);
 CHECK(!Kernel_InputBufferRead("SHORT.KIP") && Kernel_GetInputFrameCount()==frames,21);
 memset(file,0,sizeof(file));file[sizeof(sInput)]=0x80;File_Save("TRUNC.KIP",file,sizeof(sInput)+1);
 CHECK(!Kernel_InputBufferRead("TRUNC.KIP") && Kernel_GetInputFrameCount()==frames,22);
 file[sizeof(sInput)]=0xfe;file[sizeof(sInput)+1]=1;File_Save("OFFSET.KIP",file,sizeof(sInput)+2);
 CHECK(!Kernel_InputBufferRead("OFFSET.KIP"),23);
 file[sizeof(sInput)]=0;File_Save("NOEND.KIP",file,sizeof(sInput)+2);CHECK(!Kernel_InputBufferRead("NOEND.KIP"),24);
 CHECK(!Kernel_InputBufferRead("ABSENT.KIP") && !Kernel_InputBufferWrite("Z:\\BAD\\FILE.KIP"),25);
 CHECK(Kernel_InputRecordBegin(sizeof(sInput)+1),26);Kernel_InputBufferSet(&a);Kernel_InputBufferSet(&a);
 CHECK(Kernel_GetInputFrameCount()==2 && Kernel_GetInputBytes()==sizeof(sInput)+1,27);
 Kernel_InputBufferSet(&b);CHECK(Kernel_GetInputMode()==eKERNEL_INPUT_NORMAL && Kernel_GetInputFrameCount()==2,28);
 CHECK(Kernel_InputReplayBegin(),29);Kernel_InputBufferGet(&out);Kernel_InputBufferGet(&out);CHECK(!memcmp(&out,&a,sizeof(a)),30);
 CHECK(Kernel_InputRecordBegin(sizeof(sInput)+2),31);Kernel_InputBufferSet(&c);a=c;a.mKeyStatus[0]=3;Kernel_InputBufferSet(&a);
 CHECK(Kernel_GetInputFrameCount()==2 && Kernel_GetInputBytes()==sizeof(sInput)+2,32);
 CHECK(Kernel_InputReplayBegin(),33);Kernel_InputBufferGet(&out);Kernel_InputBufferGet(&out);CHECK(!memcmp(&out,&a,sizeof(a)),34);
 Kernel_DeInit();CHECK(File_GetDTA()==oldDta && Vbl_GetpVbl()->mCallCount==calls,35);
 Kernel_Init(&task,1,0,0,0);CHECK(!Kernel_GetInputFrameCount() && !Kernel_InputReplayBegin(),36);Kernel_DeInit();
 return 1;
}
S16 GodLib_Game_Main(S16 argc,char **argv)
{
 static U16 pal[16]={0,0x777};U16 dirty=2;char line[40];(void)argc;(void)argv;
 GemDos_Super(0);Platform_Init();Screen_Init(320,200,eGRAPHIC_COLOURMODE_4PLANE,0);Fade_SetPalDirect(pal);
 gInputTestPass=tests();gInputTestDone=1;
 while(!IKBD_GetKeyStatus(eIKBDSCAN_ESC)){Screen_Update();if(dirty){Screen_Logic_ClearScreen();sprintf(line,"INPUT %s / CHECK %u",gInputTestPass?"PASS":"FAIL",gInputTestStage);Font8x8_Print(line,Screen_GetpLogic(),0,16);--dirty;}}
 Screen_DeInit();Platform_DeInit();return !gInputTestPass;
}
