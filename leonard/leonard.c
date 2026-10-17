/*************************************************************************************
 * GodLib Leonard sample: channel activity with James Boulton's STF_DEMO VU bars.
 * mt_Visualizer counts retrigger age; these bars do not measure audio amplitude.
 ************************************************************************************/
#include <godlib/file/file.h>
#include <godlib/font8x8/font8x8.h>
#include <godlib/gemdos/gemdos.h>
#include <godlib/ikbd/ikbd.h>
#include <godlib/memory/memory.h>
#include <godlib/music/leonardmod.h>
#include <godlib/platform/platform.h>
#include <godlib/screen/screen.h>
#include <godlib/system/system.h>
#include <godlib/video/video.h>
#include <godlib/vbl/vbl.h>

#ifndef LEONARD_RATE
#define LEONARD_RATE eLEONARDMOD_FREQ_25K
#endif

extern U16 gLanceVisPalette[16],gStereoVisPalette[16];
extern void StereoVis_InitSplit(void *screen);
extern void StereoVis_InitMono(void *screen);
extern void StereoVis_DrawSplit(void *screen,const S8 *stereo,S8 *previous);
extern void StereoVis_DrawMono(void *screen,const S8 *stereo,S8 *previous);
extern void LanceVis_Draw(void *screen,const U16 *levels,U16 *previous);
extern void ScopeVis_Init(void *screen);
extern void ScopeVis_Draw(void *screen,const S8 *samples,S8 *previous);
S8 gLeonardVisScope[dMODSCOPE_BYTES],gLeonardVisScopePrevious[2][dMODSCOPE_BYTES];
extern void XYVis_Draw(void *screen,const S8 *stereo,U16 *previousOffsets);
S8 gLeonardVisStereo[dMODSCOPE_STEREO_BYTES];
U16 gLeonardVisXYPrevious[2][dMODSCOPE_XY_POINTS*2];
volatile U16 gLeonardVisMode; /* 0 bars, 1 four traces, 2 ICE XY, 3 stereo, 4 mono */
U16 gLeonardVisPageView[2]={0xffff,0xffff};
U16 gLeonardVisAge[4],gLeonardVisLevel[4],gLeonardVisPrevious[2][4];
volatile U16 gLeonardVisReady,gLeonardVisExited,gLeonardVisEnabled=1,gLeonardVisRaster;
volatile U32 gLeonardVisFrames,gLeonardVisLastVbl,gLeonardVisMissedVbl;
U16 *gLeonardVisScreen;
U16 gLeonardVisPage;

static void DrawScene(U16 initial)
{
    U16 i;
    static const U16 x[4]={48,208,256,96};
    sGraphicCanvas *canvas=Screen_GetpBackGraphic();
    GraphicCanvas_ClearScreen(canvas);
    Font8x8_PrintColourCanvas(LEONARD_RATE==eLEONARDMOD_FREQ_12K?
        "LEONARD / LOSTPARO.MOD / 12.5KHZ":"LEONARD / LOSTPARO.MOD / 25KHZ",canvas,32,8,1);
    if(gLeonardVisMode==3) {
        Font8x8_PrintColourCanvas("LEFT",canvas,144,24,4);
        Font8x8_PrintColourCanvas("RIGHT",canvas,144,108,8);
    } else if(gLeonardVisMode==4) {
        Font8x8_PrintColourCanvas("MONO (L+R)/2",canvas,112,48,1);
    } else if(gLeonardVisMode==2) {
        Font8x8_PrintColourCanvas("LEFT XY",canvas,52,48,2);
        Font8x8_PrintColourCanvas("RIGHT XY",canvas,208,48,2);
    } else for(i=0;i<4;++i) {
        char text[6]={(i==0 || i==3)?'L':'R',' ','C','H',(char)('1'+i),0};
        Font8x8_PrintColourCanvas(text,canvas,
            gLeonardVisMode?((i==0 || i==3)?60:220):x[i]-12,
            (gLeonardVisMode && i>=2)?108:24,2);
    }
    Font8x8_PrintColourCanvas("F1 CPU  O VISUAL V SHOW  ESC EXIT",canvas,32,192,1);
    if(initial) {
        GraphicCanvas_CopyScreen(Screen_GetpLogicGraphic(),Screen_GetpBack());
        GraphicCanvas_CopyScreen(Screen_GetpPhysicGraphic(),Screen_GetpBack());
    }
    Video_SetPalST(gLeonardVisMode>=3?gStereoVisPalette:gLanceVisPalette);
}

/* Stable debug/test boundary: frame has been rendered, audio has been mixed by the main loop. */
void LeonardVis_FrameDone(void) __attribute__((noinline));
void LeonardVis_FrameDone(void) { __asm__ volatile ("" ::: "memory"); }

S16 GodLib_Game_Main(S16 argc,char **argv)
{
    void *mod=0;
    U16 quit=0,i;
    (void)argc;(void)argv;
    GemDos_Super(0);Platform_Init();File_Init();
    if(System_GetMCH()!=MCH_STE && System_GetMCH()!=MCH_MEGASTE) {
        GemDos_Cconws("Leonard sample requires Atari STE/MegaSTE DMA sound.\r\n");
        goto done;
    }
    mod=LeonardMod_Load("LOSTPARO.MOD");
    if(!mod) {
        GemDos_Cconws("Could not load LOSTPARO.MOD\r\n");
        goto done;
    }
    Screen_Init(320,200,eGRAPHIC_COLOURMODE_4PLANE,eSCREEN_SCROLL_NONE);
    if(!gScreenClass.mpMemBase)goto unload;
    DrawScene(1);
    if(!LeonardMod_Start(mod,LEONARD_RATE)) {
        LeonardMod_Stop();
        goto screen_done;
    }
    gLeonardVisReady=1;
    while(!quit) {
        U32 now;
        Screen_Update();LeonardMod_Tick();IKBD_Update();
        now=Vbl_GetCounter();
        if(gLeonardVisFrames && now-gLeonardVisLastVbl>1)gLeonardVisMissedVbl+=now-gLeonardVisLastVbl-1;
        gLeonardVisLastVbl=now;
        while(IKBD_GetKbdBytesWaiting()) {
            U8 key=IKBD_PopKbdByte();
            if(key==eIKBDSCAN_SPACE || key==eIKBDSCAN_ESC)quit=1;
            if(key==eIKBDSCAN_F1) {
                gLeonardVisRaster^=1;LeonardMod_SetRasterDebug(gLeonardVisRaster);
            }
            if(key==eIKBDSCAN_V)gLeonardVisEnabled^=1;
            if(key==eIKBDSCAN_O) {
                gLeonardVisMode=(gLeonardVisMode+1)%5;
                DrawScene(0);
                gLeonardVisPageView[0]=gLeonardVisPageView[1]=0xffff;
            }
        }
        LeonardMod_GetVisualizer(gLeonardVisAge);
        for(i=0;i<4;++i)
            gLeonardVisLevel[i]=(gLeonardVisEnabled && gLeonardVisAge[i]<16)?16-gLeonardVisAge[i]:0;
        gLeonardVisPage=Screen_GetLogicIndex();
        gLeonardVisScreen=Screen_GetpLogic();
        {
            U16 view=gLeonardVisEnabled?gLeonardVisMode+1:0;
            if(gLeonardVisPageView[gLeonardVisPage]!=view) {
                GraphicCanvas_CopyScreen(Screen_GetpLogicGraphic(),Screen_GetpBack());
                Memory_Clear(sizeof(gLeonardVisPrevious[0]),gLeonardVisPrevious[gLeonardVisPage]);
                Memory_Clear(dMODSCOPE_BYTES,gLeonardVisScopePrevious[gLeonardVisPage]);
                for(i=0;i<dMODSCOPE_XY_POINTS*2;++i)
                    gLeonardVisXYPrevious[gLeonardVisPage][i]=0xffff;
                if(view==2)ScopeVis_Init(gLeonardVisScreen);
                if(view==4)StereoVis_InitSplit(gLeonardVisScreen);
                if(view==5)StereoVis_InitMono(gLeonardVisScreen);
                gLeonardVisPageView[gLeonardVisPage]=view;
            }
            if(view==2) {
                LeonardMod_GetOscilloscope(gLeonardVisScope);
                ScopeVis_Draw(gLeonardVisScreen,gLeonardVisScope,gLeonardVisScopePrevious[gLeonardVisPage]);
            } else if(view==3) {
                LeonardMod_GetStereoOscilloscope(gLeonardVisStereo);
                XYVis_Draw(gLeonardVisScreen,gLeonardVisStereo,gLeonardVisXYPrevious[gLeonardVisPage]);
            } else if(view>=4) {
                LeonardMod_GetStereoOscilloscope(gLeonardVisStereo);
                if(view==4)StereoVis_DrawSplit(gLeonardVisScreen,gLeonardVisStereo,gLeonardVisScopePrevious[gLeonardVisPage]);
                else StereoVis_DrawMono(gLeonardVisScreen,gLeonardVisStereo,gLeonardVisScopePrevious[gLeonardVisPage]);
            } else if(view==1) {
                LanceVis_Draw(gLeonardVisScreen,gLeonardVisLevel,gLeonardVisPrevious[gLeonardVisPage]);
            }
        }
        ++gLeonardVisFrames;
        LeonardVis_FrameDone();
    }
    LeonardMod_Stop();
screen_done:
    LeonardMod_ShutdownPaula();
    Screen_DeInit();
unload:
    LeonardMod_UnLoad(mod);
done:
    File_DeInit();Platform_DeInit();gLeonardVisExited=1;
    return 0;
}
