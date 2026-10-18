/* SNDH / PSG visualizers: GodLib SND Timer C replay, STF_DEMO and POV93. */
#include "visual.h"
#include <godlib/file/file.h>
#include <godlib/font8x8/font8x8.h>
#include <godlib/gemdos/gemdos.h>
#include <godlib/ikbd/ikbd.h>
#include <godlib/memory/memory.h>
#include <godlib/music/snd.h>
#include <godlib/platform/platform.h>
#include <godlib/screen/screen.h>
#include <godlib/video/video.h>
#include <godlib/vbl/vbl.h>
#include <godlib/string/string.h>

void (*gSndVisPlay)(void);
volatile U16 gSndVisMode,gSndVisRaster,gSndVisReady,gSndVisExited,gSndVisEnabled=1;
volatile U32 gSndVisFrames,gSndVisMissedVbl,gSndVisLastVbl;
U16 gSndVisPageView[2]={0xffff,0xffff},gSndVisBarsOld[2][3];
U8 gSndVisBandsOld[2][80],gSndVisPianoOld[2][80];
U16 gSndVisRingOld[2][12],gSndVisScopeOld[2][6];
static U16 sSpectrumPalette[16]={0,0x077,0x777};
static U16 sExtraPalette[16]={0,0xfff,0x222,0x444,0,0,0,0,0,0xf00,0x0f0,0xff0,0x00f,0xf0f,0x0ff,0xfff};
static U16 sOrganPalette[16]={0,0,0,0,0,0,0,0,0,0xf00,0x0f0,0xff0,0x00f,0xf0f,0x0ff,0xfff};
static U16 sScopePalette[16]={0,0xf00,0x0f0,0xff0,0x00f,0xf0f,0x0ff,0xfff,0x222,0xf00,0x0f0,0xff0,0x00f,0xf0f,0x0ff,0xfff};

static void Scene(U16 initial)
{
 U16 i; sGraphicCanvas *canvas=Screen_GetpBackGraphic();
 GraphicCanvas_ClearScreen(canvas);
 Font8x8_PrintColourCanvas("SNDH / POPCORN / MODMATE",canvas,64,8,gSndVisMode>=2?15:2);
 if(gSndVisMode==1){
  Font8x8_PrintColourCanvas("80 NOTE BANDS / MIRRORED",canvas,64,40,2);
  Font8x8_PrintColourCanvas("C1",canvas,8,128,2);
  Font8x8_PrintColourCanvas("G7",canvas,296,128,2);
 }else if(gSndVisMode==0){
  for(i=0;i<3;++i){char label[2]={'A'+i,0};Font8x8_PrintColourCanvas(label,canvas,120+32*i,24,2);}
 }
 if(gSndVisMode>=2){
  static const char *title[4]={"PIANO / C1-G7","SYNTHETIC PSG / 10.24 MS","NOTE CHANGES / EXPANDING RINGS","COLOUR ORGAN / RGB"};
  Font8x8_PrintColourCanvas(title[gSndVisMode-2],canvas,(40-String_StrLen(title[gSndVisMode-2]))/2*8,32,15);
  if(gSndVisMode==2)PsgPiano_Init(Screen_GetpBack());
  if(gSndVisMode==5)PsgOrgan_Init(Screen_GetpBack());
  for(i=0;i<3;++i){char label[2]={'A'+i,0};Font8x8_PrintColourCanvas(label,canvas,gSndVisMode==3?8:80+80*i,gSndVisMode==3?60+40*i:152,gSndVisMode==3?(1<<i):9+i+(i==2));}
 }
 Font8x8_PrintColourCanvas("ENV=MAX / FIXED 0..15",canvas,80,184,gSndVisMode>=2?15:2);
 Font8x8_PrintColourCanvas("F1 CPU  O VISUAL V SHOW  ESC EXIT",canvas,32,192,gSndVisMode>=2?15:2);
 if(initial){GraphicCanvas_CopyScreen(Screen_GetpLogicGraphic(),Screen_GetpBack());GraphicCanvas_CopyScreen(Screen_GetpPhysicGraphic(),Screen_GetpBack());}
 Video_SetPalST(gSndVisMode==5?sOrganPalette:gSndVisMode==0?gPsgBarsPalette:gSndVisMode==1?sSpectrumPalette:gSndVisMode==3||gSndVisMode==4?sScopePalette:sExtraPalette);
 gSndVisPageView[0]=gSndVisPageView[1]=0xffff;
}
static void Idle(void){}
void SndVis_FrameDone(void) __attribute__((noinline));
void SndVis_FrameDone(void){__asm__ volatile("" ::: "memory");}
S16 GodLib_Game_Main(S16 argc,char **argv)
{
 void *tune=0;U16 quit=0;U32 size;sSndInfo info;
 (void)argc;(void)argv;
 GemDos_Super(0);Platform_Init();File_Init();
 size=File_GetSize("popcorn.snd");
 if(size<1024 || !(tune=File_Load("popcorn.snd")))goto done;
 if(((sSndHeader*)tune)->mID!=mSTRING_TO_U32('S','N','D','H'))goto unload;
 Snd_GetInfo(tune,&info);
 if(info.mTimer.mType!=eSND_TIMER_C || !info.mTimer.mFreq || info.mTimer.mFreq>200){
  GemDos_Cconws("This example requires unpacked TC SNDH, 1..200 Hz.\r\n");goto unload;
 }
 Screen_Init(320,200,eGRAPHIC_COLOURMODE_4PLANE,0);
 if(!gScreenClass.mpMemBase)goto unload;
 PsgExtra_Init();Scene(1);Snd_Init();Snd_SetpChaserFunc(PsgVis_Snapshot);
 Snd_TuneInit(&info,1);gSndVisPlay=info.mPlay;Snd_SetpPlayFunc(PsgVis_Replay);
 gSndVisReady=1;
 while(!quit){
  U16 page,view,i;U32 now;
  Screen_Update();IKBD_Update();now=Vbl_GetCounter();
  if(gSndVisFrames && now-gSndVisLastVbl>1)gSndVisMissedVbl+=now-gSndVisLastVbl-1;
  gSndVisLastVbl=now;
  while(IKBD_GetKbdBytesWaiting()){
   U8 key=IKBD_PopKbdByte();
   if(key==eIKBDSCAN_SPACE || key==eIKBDSCAN_ESC)quit=1;
   if(key==eIKBDSCAN_O){gSndVisMode=(gSndVisMode+1)%6;Scene(0);}
   if(key==eIKBDSCAN_V)gSndVisEnabled^=1;
   if(key==eIKBDSCAN_F1)gSndVisRaster^=1;
  }
  PsgVis_Update();PsgExtra_Update();page=Screen_GetLogicIndex();view=gSndVisMode==5?6:gSndVisEnabled?gSndVisMode+1:0;
  if(view!=gSndVisPageView[page]){
   GraphicCanvas_CopyScreen(Screen_GetpLogicGraphic(),Screen_GetpBack());
   Memory_Clear(sizeof(gSndVisBarsOld[page]),gSndVisBarsOld[page]);
   Memory_Clear(sizeof(gSndVisBandsOld[page]),gSndVisBandsOld[page]);
   Memory_Clear(sizeof(gSndVisPianoOld[page]),gSndVisPianoOld[page]);
   for(i=0;i<6;++i)gSndVisScopeOld[page][i]=0xffff;
   Memory_Clear(sizeof(gSndVisRingOld[page]),gSndVisRingOld[page]);gSndVisPageView[page]=view;
  }
  if(view==1)PsgBars_Draw(Screen_GetpLogic(),gPsgLevels,gSndVisBarsOld[page]);
  if(view==2)PsgSpectrum_Draw(Screen_GetpLogic(),gPsgBands,gSndVisBandsOld[page]);
  if(view==3)PsgPiano_Draw(Screen_GetpLogic(),gPianoKeys,gSndVisPianoOld[page]);
  if(view==4){PsgScope_Prepare();PsgScope_Draw(Screen_GetpLogic(),gScopeParams,gSndVisScopeOld[page]);}
  if(view==5)PsgCircles_Draw(Screen_GetpLogic(),gRingAges,gSndVisRingOld[page]);
  if(view==6)PsgOrgan_Update(gSndVisEnabled?gPsgLevels:0);
  ++gSndVisFrames;SndVis_FrameDone();
 }
 Snd_TuneDeInit(&info);Snd_SetpChaserFunc(Idle);Snd_SetpPlayFunc(Idle);Snd_DeInit();
 Screen_DeInit();
unload: File_UnLoad(tune);
done: File_DeInit();Platform_DeInit();gSndVisExited=1;return 0;
}
