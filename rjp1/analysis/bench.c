/* Same state/input for original+polling and direct native replay, once per VBL. */
#include <godlib/music/rjp1.h>
#include <godlib/music/paulamixer.h>
#include <godlib/platform/platform.h>
#include <godlib/file/file.h>
#include <godlib/screen/screen.h>
#include <godlib/gemdos/gemdos.h>
#include <godlib/vbl/vbl.h>
#include <godlib/system/system.h>
#include <godlib/ikbd/ikbd.h>
#include <string.h>
extern void vd_init(void*,void*),vd_start_song(U16),vd_tick(void),vd_translate_init(void),vd_translate(void),RjpCore_Tick(void);
volatile U32 gBenchTicks;
volatile U16 gBenchReady;
static void tick(void)
{U8 save[80];memcpy(save,PaulaMixer_Channels,80);vd_tick();vd_translate();memcpy(PaulaMixer_Channels,save,80);RjpCore_Tick();++gBenchTicks;}
S16 GodLib_Game_Main(S16 argc,char **argv)
{void *a,*b;sRjp1Song *s;U16 mask;(void)argc;(void)argv;
 GemDos_Super(0);Platform_Init();File_Init();Screen_Init(320,200,eGRAPHIC_COLOURMODE_4PLANE,0);
 a=File_Load("JON.SNG");b=File_Load("JON.INS");s=Rjp1_Create(a,File_GetSize("JON.SNG"),b,File_GetSize("JON.INS"));
 if(!s)goto done;
 vd_init(a,b);vd_start_song(1);vd_translate_init();
 if(!Rjp1_Start(s,1,2))goto unload;
 mask=System_GetIML();System_SetIML(7);Vbl_RemoveCall(Rjp1_Tick);Vbl_AddCall(tick);System_SetIML(mask);gBenchReady=1;
 while(!IKBD_GetKeyStatus(eIKBDSCAN_ESC))Screen_Update();
 mask=System_GetIML();System_SetIML(7);Vbl_RemoveCall(tick);System_SetIML(mask);
unload:Rjp1_UnLoad(s);
done:if(a)File_UnLoad(a);if(b)File_UnLoad(b);Screen_DeInit();File_DeInit();Platform_DeInit();return 0;}
