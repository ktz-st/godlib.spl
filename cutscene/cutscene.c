/* Native GodLib text cutscene parser + script player; self-contained assets. */
#include <godlib/cutscene/cutparse.h>
#include <godlib/audio/amixer.h>
#include <godlib/cutscene/cut_sys.h>
#include <godlib/fade/fade.h>
#include <godlib/font/font.h>
#include <godlib/font8x8/font8x8.h>
#include <godlib/gemdos/gemdos.h>
#include <godlib/ikbd/ikbd.h>
#include <godlib/memory/memory.h>
#include <godlib/pictypes/degas.h>
#include <godlib/platform/platform.h>
#include <godlib/screen/screen.h>
#include <godlib/sprite/sprite.h>
#include <godlib/string/string.h>
#include <godlib/system/system.h>
#include <godlib/video/video.h>
extern sDegas Cut_Castle,Cut_Forest;
extern U8 Cut_Voice0[],Cut_Voice0End[],Cut_Voice1[],Cut_Voice1End[];
extern U8 Cut_Voice2[],Cut_Voice2End[],Cut_Voice3[],Cut_Voice3End[];
static sAudioDmaSound sNarration[4];
volatile U16 gCutAudio[4];
extern U16 Cut_FontSheet[],Cut_StarData[];
extern char Cut_Script[],Cut_ScriptEnd[];
sCutScene *gCutScene;
sFont *gCutFont;
sSpriteBlock *gCutStars;
volatile U16 gCutReady,gCutExited,gCutDone,gCutCallbacks,gCutResult;
volatile U16 gCutSpriteFrame;
volatile S16 gCutSpriteX,gCutSpriteY;
volatile U32 gCutTicks,gCutReplays;
static U16 sEndPages;
static U16 sEndPalette[16]={0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0xfff};

static sFont *MakeFont(void)
{
 sSpriteBlock *block=Sprite_BlockCreate(127);sFont *font=0;U8 map[128];U16 i;
 if(!block)return 0;
 for(i=0;i<127;++i){
  U16 c=i+1;U32 offset=(U32)(c/20)*6*80+(c%20)*4;
  U16 *mask=Sprite_MaskCreate(Cut_FontSheet+offset,16,6,4,4,0);
  block->mpSprite[i]=Sprite_Create(Cut_FontSheet+offset,mask,16,6,4,4,0);
  Sprite_MaskDestroy(mask);map[i]=(U8)c;
  if(!block->mpSprite[i]){Sprite_BlockDestroy(block);return 0;}
 }
 map[127]=0;font=Font_Create(block,map,6);Sprite_BlockDestroy(block);
 if(font){font->mSpaceWidth=6;font->mKerning=0;font->mWidthMax=6;font->mHeightMax=6;}
 return font;
}
static sSpriteBlock *MakeStars(void)
{
 sSpriteBlock *block=Sprite_BlockCreate(3);U16 i;
 if(!block)return 0;
 for(i=0;i<3;++i){
  U16 *data=Cut_StarData+i*80;
  sSprite *sprite=(sSprite*)mMEMCALLOC(sizeof(sSprite));
  block->mpSprite[i]=sprite;
  if(!sprite){Sprite_BlockDestroy(block);return 0;}
  sprite->mpMask=data;sprite->mpGfx=data+16;
  sprite->mWidth=16;sprite->mHeight=16;
  sprite->mGfxPlaneCount=4;sprite->mMaskPlaneCount=4;
 }
 return block;
}
static void PrepareBackdrops(void)
{
 U16 i;sDegas *pictures[2]={&Cut_Castle,&Cut_Forest};
 for(i=0;i<2;++i){
  sGraphicCanvas canvas=*Screen_GetpBackGraphic();canvas.mpVRAM=pictures[i]->mPixels;
  Font8x8_PrintColourCanvas("MOONLIT PASSAGE / GODLIB CUTSCENE",&canvas,9,5,0);
  Font8x8_PrintColourCanvas("MOONLIT PASSAGE / GODLIB CUTSCENE",&canvas,8,4,15);
  Font8x8_PrintColourCanvas("SPACE SKIP/REPLAY  R RESTART  ESC EXIT",&canvas,8,192,15);
 }
}
static U16 BindAssets(void)
{
 U16 i;U8 *starts[4]={Cut_Voice0,Cut_Voice1,Cut_Voice2,Cut_Voice3};
 U8 *ends[4]={Cut_Voice0End,Cut_Voice1End,Cut_Voice2End,Cut_Voice3End};
 for(i=0;i<4;++i){sNarration[i].mpSound=starts[i];sNarration[i].mLength=(U32)(ends[i]-starts[i]);sNarration[i].mFreq=eAUDIO_FREQ_12;sNarration[i].mBits=eAUDIO_BITS_8;}
 for(i=0;i<gCutScene->mAssetCount;++i){
  sCutAsset *asset=&gCutScene->mpAssets[i];
  if(!String_StrCmpi(asset->mpName,"BG_CASTLE"))asset->mpData=&Cut_Castle;
  else if(!String_StrCmpi(asset->mpName,"BG_FOREST"))asset->mpData=&Cut_Forest;
  else if(!String_StrCmpi(asset->mpName,"TWINKLE"))asset->mpData=gCutStars;
  else if(!String_StrCmpi(asset->mpName,"SMALL_FONT"))asset->mpData=gCutFont;
  else if(!String_StrCmpi(asset->mpName,"VOICE_ARRIVAL"))asset->mpData=&sNarration[0];
  else if(!String_StrCmpi(asset->mpName,"VOICE_PATH"))asset->mpData=&sNarration[1];
  else if(!String_StrCmpi(asset->mpName,"VOICE_FOREST"))asset->mpData=&sNarration[2];
  else if(!String_StrCmpi(asset->mpName,"VOICE_JOURNEY"))asset->mpData=&sNarration[3];
  else return 0;
 }
 return 1;
}
static void StartScene(void)
{
 CutScene_System_Stop();
 Fade_SetPalDirect(Fade_GetpBlackPal());
 Memory_Clear(32000,Screen_GetpBack());Memory_Clear(32000,Screen_GetpLogic());Memory_Clear(32000,Screen_GetpPhysic());
 gCutDone=0;gCutCallbacks=0;gCutResult=0;sEndPages=0;++gCutReplays;
 CutScene_System_ScriptInit(gCutScene,"MAIN");
}
static void FinishScene(void)
{
 CutScene_System_Stop();gCutDone=1;sEndPages=0;
 Memory_Clear(32000,Screen_GetpLogic());Memory_Clear(32000,Screen_GetpPhysic());
 Fade_SetPalDirect(sEndPalette);
}
void CutExample_FrameDone(void) __attribute__((noinline));
void CutExample_FrameDone(void){__asm__ volatile("" ::: "memory");}
S16 GodLib_Game_Main(S16 argc,char **argv)
{
 U16 quit=0,error=0;(void)argc;(void)argv;
 GemDos_Super(0);Platform_Init();Screen_Init(320,200,eGRAPHIC_COLOURMODE_4PLANE,0);
 if(!Screen_GetpMemBase()){Platform_DeInit();return 1;}
 Graphic_SetBlitterEnable(System_GetBLT()==BLT_BLITTER);
 AudioMixer_Init();AudioMixer_SetFrequency(eAUDIO_FREQ_12);AudioMixer_Enable();
 CutScene_System_AppInit();
 PrepareBackdrops();gCutFont=MakeFont();gCutStars=MakeStars();
 gCutScene=CutScene_Parse(Cut_Script,(U32)(Cut_ScriptEnd-Cut_Script));
 if(!gCutFont||!gCutStars||!gCutScene||!BindAssets()){error=1;goto cleanup;}
 StartScene();gCutReady=1;
 while(!quit){
  Screen_Update();IKBD_Update();
  while(IKBD_GetKbdBytesWaiting()){
   U8 key=IKBD_PopKbdByte();
   if(key==eIKBDSCAN_ESC)quit=1;
   else if(key==eIKBDSCAN_R || (key==eIKBDSCAN_SPACE && gCutDone))StartScene();
   else if(key==eIKBDSCAN_SPACE)FinishScene();
  }
  if(!gCutDone){
   gCutResult=CutScene_System_Update();CutScene_System_Render();
   if(gCutResult==2)++gCutCallbacks;
   if(gCutResult==1)FinishScene();
   gCutSpriteX=gCutScene->mpSprites[0].mCurrentDef.mX;
   gCutSpriteY=gCutScene->mpSprites[0].mCurrentDef.mY;
   gCutSpriteFrame=gCutScene->mpSprites[0].mAnimFrame.w.w1;
  }else if(!(sEndPages&(1<<Screen_GetLogicIndex()))){
   sGraphicCanvas *canvas=Screen_GetpLogicGraphic();
   Font8x8_PrintColourCanvas("THE END",canvas,132,80,15);
   Font8x8_PrintColourCanvas("SPACE TO REPLAY / ESC TO EXIT",canvas,48,112,15);
   sEndPages|=1<<Screen_GetLogicIndex();
  }
  {U16 i;for(i=0;i<4;++i)gCutAudio[i]=CutScene_System_IsSamplePlaying(&gCutScene->mpSamples[i]);}
  ++gCutTicks;CutExample_FrameDone();
 }
cleanup:
 CutScene_System_AppInit();CutScene_System_AppDeInit();
 if(gCutScene){mMEMFREE(gCutScene);gCutScene=0;}
 if(gCutStars){Sprite_BlockDestroy(gCutStars);gCutStars=0;}
 if(gCutFont){Font_Destroy(gCutFont);gCutFont=0;}
 AudioMixer_DeInit();Screen_DeInit();Platform_DeInit();gCutExited=1;
 return error;
}
