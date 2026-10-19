/* Reuse the example's native font factory and embedded assets, not its player. */
#define GodLib_Game_Main CutExample_UnusedMain
#include "../cutscene.c"
#undef GodLib_Game_Main
#include <godlib/vbl/vbl.h>
#include <godlib/cutscene/cutparse.h>
extern sAmixerSpl gAudioMixerSamples[2];
volatile U16 gTestStage,gTestAdvance,gTestError,gTestDone;
volatile U32 gTestFeatureError;
static sCutScene test;
static sCutScript script;
static sCutCommand commands[16];
static sCutAsset assets[4];
static sCutText caption;
static sCutPage pages[2];
static sCutSample samples[3];
static U8 pcm[250]={127};
static sAudioDmaSound sound;
static char longword[260];
void __attribute__((noinline)) CutTest_Marker(void){__asm__ volatile("" ::: "memory");}
static void mark(U16 stage)
{gTestStage=stage;gTestAdvance=0;while(!gTestAdvance)CutTest_Marker();}
static void command(U16 i,U16 op,void *arg,void *arg1)
{commands[i].mOp=op;commands[i].mArg0=(U32)arg;commands[i].mArg1=(U32)arg1;}
static void begin(U16 count)
{script.mCommandCount=count;CutScene_System_ScriptInit(&test,"MAIN");}
static void renderBoth(void)
{CutScene_System_Render();CutScene_System_Render();Screen_Update();CutScene_System_Render();}
S16 GodLib_Game_Main(S16 argc,char **argv)
{
 U16 i; sCutScene *parsed;
 (void)argc;(void)argv;GemDos_Super(0);Platform_Init();Screen_Init(320,200,eGRAPHIC_COLOURMODE_4PLANE,0);
 AudioMixer_Init();AudioMixer_SetFrequency(eAUDIO_FREQ_12);AudioMixer_Enable();CutScene_System_AppInit();
 gCutFont=MakeFont();if(!gCutFont){gTestError=1;goto done;}
 test.mpAssets=assets;test.mAssetCount=4;test.mpScripts=&script;test.mScriptCount=1;
 test.mpTexts=&caption;test.mTextCount=1;test.mpPages=pages;test.mPageCount=2;test.mpSamples=samples;test.mSampleCount=3;
 script.mpName="MAIN";script.mpCommands=commands;assets[0].mpData=&Cut_Castle;assets[1].mpData=gCutFont;
 caption.mInitialDef.mpAsset=&assets[1];caption.mInitialDef.mpPage=&pages[0];
 caption.mInitialDef.mRect.mX=100;caption.mInitialDef.mRect.mY=30;caption.mInitialDef.mRect.mWidth=60;caption.mInitialDef.mRect.mHeight=40;
 pages[0].mpText="AB\r\nCD\tE\nFG";pages[1].mpText="HI JK LM NO PQ";
 command(0,eCUT_CMD_BG_GFX_SET,&assets[0],0);command(1,eCUT_CMD_TEXT_ENABLE,&caption,0);command(2,eCUT_CMD_CALLBACK,0,0);command(3,eCUT_CMD_WAIT,(void*)1000,0);command(4,eCUT_CMD_RETURN,0,0);
 begin(5);CutScene_System_Update();CutScene_System_Render();CutScene_System_Render();Screen_Update();CutScene_System_Update();CutScene_System_Render();
 if(CutScene_System_Update()!=2)gTestError|=2;
 renderBoth();mark(1);
 /* Change text while still enabled; correct width is X+WIDTH, not WIDTH. */
 command(3,eCUT_CMD_TEXT_PAGE_SET,&caption,&pages[1]);command(4,eCUT_CMD_CALLBACK,0,0);script.mCommandCount=5;
 CutScene_System_Update();renderBoth();mark(2);
 /* Clearing the background replaces Back and both pages with zeros. */
 command(0,eCUT_CMD_BG_GFX_CLEAR,0,0);command(1,eCUT_CMD_CALLBACK,0,0);begin(2);
 CutScene_System_Update();CutScene_System_Render();Screen_Update();CutScene_System_Update();CutScene_System_Render();CutScene_System_Update();mark(3);
 for(i=0;i<259;++i)longword[i]='A';
 longword[259]=0;pages[0].mpText=longword;
 command(0,eCUT_CMD_TEXT_ENABLE,&caption,0);command(1,eCUT_CMD_CALLBACK,0,0);begin(2);CutScene_System_Update();renderBoth();mark(4);
 /* Background visibility preserves the selected asset and all overlays. */
 pages[0].mpText="AB CD EFGH";pages[1].mpText="HI JK";
 caption.mInitialDef.mRect.mWidth=42;assets[3].mpData=&Cut_Forest;
 command(0,eCUT_CMD_BG_GFX_SET,&assets[0],0);command(1,eCUT_CMD_TEXT_ENABLE,&caption,0);command(2,eCUT_CMD_CALLBACK,0,0);
 begin(3);CutScene_System_Update();renderBoth();CutScene_System_Update();renderBoth();mark(6);
 command(3,eCUT_CMD_BG_GFX_DISABLE,0,0);command(4,eCUT_CMD_CALLBACK,0,0);script.mCommandCount=5;
 if(CutScene_System_Update()!=0)gTestFeatureError|=1;
 CutScene_System_Render();CutScene_System_Render();
 if(CutScene_System_Update()!=0)gTestFeatureError|=2; /* other page still dirty */
 Screen_Update();CutScene_System_Render();if(CutScene_System_Update()!=2)gTestFeatureError|=4;
 renderBoth();mark(7);
 command(5,eCUT_CMD_BG_GFX_SET,&assets[3],0);command(6,eCUT_CMD_CALLBACK,0,0);script.mCommandCount=7;
 CutScene_System_Update();renderBoth();CutScene_System_Update();renderBoth();mark(8);
 command(7,eCUT_CMD_BG_GFX_ENABLE,0,0);command(8,eCUT_CMD_CALLBACK,0,0);script.mCommandCount=9;
 CutScene_System_Update();renderBoth();CutScene_System_Update();renderBoth();mark(9);
 command(9,eCUT_CMD_BG_GFX_ENABLE,0,0);command(10,eCUT_CMD_CALLBACK,0,0);script.mCommandCount=11;
 if(CutScene_System_Update()!=2)gTestFeatureError|=8; /* repeated enable is a no-op */
 /* Letter reveal: delay=2, blank first frame, stable complete-word wrapping. */
 command(0,eCUT_CMD_BG_GFX_SET,&assets[0],0);command(1,eCUT_CMD_TEXT_ANIM_SET,&caption,(void*)2);
 command(2,eCUT_CMD_TEXT_ENABLE,&caption,0);command(3,eCUT_CMD_TEXT_ANIM_WAIT,&caption,0);
 command(4,eCUT_CMD_CALLBACK,0,0);command(5,eCUT_CMD_WAIT,(void*)10000,0);
 begin(6);CutScene_System_Update();renderBoth();CutScene_System_Update();renderBoth();
 if(caption.mOffset || caption.mWordPauseConstant!=2)gTestFeatureError|=16;
 if(CutScene_System_Update()!=0 || caption.mOffset)gTestFeatureError|=32;
 renderBoth();mark(10);
 for(i=0;i<13;++i){if(CutScene_System_Update()!=0)gTestFeatureError|=64;renderBoth();}
 if(caption.mOffset!=7)gTestFeatureError|=128;
 mark(11);
 for(i=0;i<5;++i){CutScene_System_Update();renderBoth();}
 if(CutScene_System_Update()!=0 || caption.mOffset!=10)gTestFeatureError|=256;
 CutScene_System_Render();CutScene_System_Render();
 if(CutScene_System_Update()!=0)gTestFeatureError|=512; /* WAIT needs final glyph on both pages */
 Screen_Update();CutScene_System_Render();
 if(CutScene_System_Update()!=2)gTestFeatureError|=1024;
 renderBoth();mark(12);
 command(5,eCUT_CMD_TEXT_PAGE_SET,&caption,&pages[1]);command(6,eCUT_CMD_TEXT_ANIM_WAIT,&caption,0);
 command(7,eCUT_CMD_CALLBACK,0,0);command(8,eCUT_CMD_WAIT,(void*)10000,0);script.mCommandCount=9;
 if(CutScene_System_Update()!=0 || caption.mOffset)gTestFeatureError|=2048;
 renderBoth();mark(13);
 for(i=0;i<10;++i){if(CutScene_System_Update()!=0)gTestFeatureError|=4096;renderBoth();}
 if(CutScene_System_Update()!=2 || caption.mOffset!=5)gTestFeatureError|=8192;
 renderBoth();mark(14);
 /* Zero switches a live animation to immediate full text and waits for redraw. */
 command(0,eCUT_CMD_BG_GFX_SET,&assets[0],0);command(1,eCUT_CMD_TEXT_ANIM_SET,&caption,(void*)3);
 command(2,eCUT_CMD_TEXT_ENABLE,&caption,0);command(3,eCUT_CMD_CALLBACK,0,0);
 command(4,eCUT_CMD_TEXT_ANIM_SET,&caption,0);command(5,eCUT_CMD_TEXT_ANIM_WAIT,&caption,0);command(6,eCUT_CMD_CALLBACK,0,0);
 begin(7);CutScene_System_Update();renderBoth();CutScene_System_Update();renderBoth();
 if(CutScene_System_Update()!=0 || caption.mWordPauseConstant)gTestFeatureError|=16384;
 renderBoth();if(CutScene_System_Update()!=2)gTestFeatureError|=32768;
 renderBoth();mark(15);
 /* Empty/disabled text cannot deadlock a wait; restart clears animation state. */
 pages[0].mpText="";
 command(0,eCUT_CMD_TEXT_ANIM_SET,&caption,(void*)2);command(1,eCUT_CMD_TEXT_ENABLE,&caption,0);
 command(2,eCUT_CMD_TEXT_ANIM_WAIT,&caption,0);command(3,eCUT_CMD_CALLBACK,0,0);begin(4);
 if(CutScene_System_Update()!=2)gTestFeatureError|=65536UL;
 pages[0].mpText="AB CD EFGH";command(1,eCUT_CMD_TEXT_ANIM_WAIT,&caption,0);command(2,eCUT_CMD_CALLBACK,0,0);begin(3);
 if(caption.mWordPauseConstant || caption.mOffset)gTestFeatureError|=131072UL;
 if(CutScene_System_Update()!=2)gTestFeatureError|=262144UL;
 CutScene_System_Stop();if(!CutScene_System_IsScriptFinished()||CutScene_System_Update()!=1)gTestError|=4;
 begin(0);if(CutScene_System_Update()!=1 || !CutScene_System_IsScriptFinished())gTestError|=8;
 CutScene_System_ScriptInit(&test,"ABSENT");if(CutScene_System_Update()!=1 || !CutScene_System_IsScriptFinished())gTestError|=16;
 command(0,eCUT_CMD_CALL,&script,0);begin(1);if(CutScene_System_Update()!=1 || !CutScene_System_IsScriptFinished())gTestError|=32;
 {char text[]="<VAR NAME=\"V\">\n{\nVARNAME=\"scene.flag\"\n}\n";parsed=CutScene_Parse(text,sizeof(text)-1);}
 if(!parsed || parsed->mVarCount!=1)gTestError|=64;
 if(parsed)mMEMFREE(parsed);
 sound.mpSound=pcm;sound.mLength=250;sound.mFreq=eAUDIO_FREQ_12;sound.mBits=eAUDIO_BITS_8;sound.mStereoFlag=0;sound.mLoopingFlag=0;assets[2].mpData=&sound;
 for(i=0;i<3;++i){samples[i].mpAsset=&assets[2];samples[i].mVolume=200-i*50;samples[i].mStereoPos=i?255:0;samples[i].mFlagLoop=1;}
 command(0,eCUT_CMD_SAMPLE_ENABLE,&samples[0],0);command(1,eCUT_CMD_SAMPLE_ENABLE,&samples[1],0);command(2,eCUT_CMD_CALLBACK,0,0);begin(3);CutScene_System_Update();
 if(!CutScene_System_IsSamplePlaying(&samples[0]) || !CutScene_System_IsSamplePlaying(&samples[1]))gTestError|=128;
 if(!AudioMixer_IsVoicePlaying(0)||!AudioMixer_IsVoicePlaying(1))gTestError|=256;
 if(gAudioMixerSamples[0].mVolume!=200 || gAudioMixerSamples[0].mGainLeft!=200 || gAudioMixerSamples[0].mGainRight || gAudioMixerSamples[1].mVolume!=150 || gAudioMixerSamples[1].mGainLeft || gAudioMixerSamples[1].mGainRight!=150)gTestError|=256;
 for(i=0;i<4;++i)Vbl_WaitVbl();
 {U16 any=0;for(i=0;i<8192;++i)any|=AudioMixer_GetpBuffer()[i];if(!any)gTestError|=2048;}
 command(0,eCUT_CMD_SAMPLE_ENABLE,&samples[2],0);command(1,eCUT_CMD_SAMPLE_WAIT,&samples[2],0);
 /* Resume the same script without a ScriptInit, retaining both live voices. */
 command(3,eCUT_CMD_SAMPLE_ENABLE,&samples[2],0);command(4,eCUT_CMD_SAMPLE_DISABLE,&samples[1],0);command(5,eCUT_CMD_CALLBACK,0,0);script.mCommandCount=6;CutScene_System_Update();
 if(CutScene_System_IsSamplePlaying(&samples[0]) || CutScene_System_IsSamplePlaying(&samples[1]) || !CutScene_System_IsSamplePlaying(&samples[2]))gTestError|=512;
if(AudioMixer_IsVoicePlaying(1))gTestError|=512;
 command(6,eCUT_CMD_SAMPLE_DISABLE,&samples[2],0);command(7,eCUT_CMD_CALLBACK,0,0);script.mCommandCount=8;CutScene_System_Update();
 CutScene_System_Stop();if(AudioMixer_IsVoicePlaying(0)||AudioMixer_IsVoicePlaying(1))gTestError|=1024;
 for(i=0;i<8192;++i)if(AudioMixer_GetpBuffer()[i])gTestError|=2048;
 /* A one-shot wait blocks until the source and the queued tail finish. */
 samples[0].mFlagLoop=0;sound.mLoopingFlag=1;command(0,eCUT_CMD_SAMPLE_ENABLE,&samples[0],0);command(1,eCUT_CMD_SAMPLE_WAIT,&samples[0],0);command(2,eCUT_CMD_CALLBACK,0,0);command(3,eCUT_CMD_RETURN,0,0);begin(4);
 if(CutScene_System_Update()!=0)gTestError|=4096;
 for(i=0;i<30;++i){Vbl_WaitVbl();if(CutScene_System_Update()==2)break;}
 if(i==30 || i<3)gTestError|=8192;
 if(CutScene_System_Update()!=1 || !CutScene_System_IsScriptFinished())gTestError|=16384;
 CutScene_System_AppDeInit();
 done:
 if(gCutFont)Font_Destroy(gCutFont);
 AudioMixer_DeInit();Screen_DeInit();Platform_DeInit();gTestDone=1;mark(5);return 0;
}
