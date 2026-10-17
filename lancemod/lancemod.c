/*************************************************************************************
 * GodLib LanceMod sample: channel activity with James Boulton's STF_DEMO VU bars.
 * mt_Visualizer counts retrigger age; these bars do not measure audio amplitude.
 ************************************************************************************/
#include <godlib/file/file.h>
#include <godlib/font8x8/font8x8.h>
#include <godlib/gemdos/gemdos.h>
#include <godlib/ikbd/ikbd.h>
#include <godlib/memory/memory.h>
#include <godlib/music/lancemod.h>
#include <godlib/platform/platform.h>
#include <godlib/screen/screen.h>
#include <godlib/system/system.h>
#include <godlib/video/video.h>
#include <godlib/vbl/vbl.h>

extern U16 gLanceVisPalette[16],gStereoVisPalette[16];
extern void StereoVis_InitSplit(void *screen);
extern void StereoVis_InitMono(void *screen);
extern void StereoVis_DrawSplit(void *screen,const S8 *stereo,S8 *previous);
extern void StereoVis_DrawMono(void *screen,const S8 *stereo,S8 *previous);
extern void LanceVis_Draw(void *screen,const U16 *levels,U16 *previous);
extern void ScopeVis_Init(void *screen);
extern void ScopeVis_Draw(void *screen,const S8 *samples,S8 *previous);
S8 gLanceVisScope[dMODSCOPE_BYTES],gLanceVisScopePrevious[2][dMODSCOPE_BYTES];
extern void XYVis_Draw(void *screen,const S8 *stereo,U16 *previousOffsets);
S8 gLanceVisStereo[dMODSCOPE_STEREO_BYTES];
U16 gLanceVisXYPrevious[2][dMODSCOPE_XY_POINTS*2];
volatile U16 gLanceVisMode; /* 0 bars, 1 four traces, 2 ICE XY, 3 stereo, 4 mono */
U16 gLanceVisPageView[2]={0xffff,0xffff};
U16 gLanceVisAge[4],gLanceVisLevel[4],gLanceVisPrevious[2][4];
volatile U16 gLanceVisReady,gLanceVisExited,gLanceVisEnabled=1,gLanceVisRaster;
volatile U32 gLanceVisFrames,gLanceVisLastVbl,gLanceVisMissedVbl;
U16 *gLanceVisScreen;
U16 gLanceVisPage;

static void DrawScene(U16 initial)
{
    U16 i;
    static const U16 x[4]={48,208,256,96};
    sGraphicCanvas *canvas=Screen_GetpBackGraphic();
    GraphicCanvas_ClearScreen(canvas);
    Font8x8_PrintColourCanvas("LANCEMOD / LOSTPARO.MOD / 25KHZ",canvas,40,8,1);
    if(gLanceVisMode==3) {
        Font8x8_PrintColourCanvas("LEFT",canvas,144,24,4);
        Font8x8_PrintColourCanvas("RIGHT",canvas,144,108,8);
    } else if(gLanceVisMode==4) {
        Font8x8_PrintColourCanvas("MONO (L+R)/2",canvas,112,48,1);
    } else if(gLanceVisMode==2) {
        Font8x8_PrintColourCanvas("LEFT XY",canvas,52,48,2);
        Font8x8_PrintColourCanvas("RIGHT XY",canvas,208,48,2);
    } else for(i=0;i<4;++i) {
        char text[6]={(i==0 || i==3)?'L':'R',' ','C','H',(char)('1'+i),0};
        Font8x8_PrintColourCanvas(text,canvas,
            gLanceVisMode?((i==0 || i==3)?60:220):x[i]-12,
            (gLanceVisMode && i>=2)?108:24,2);
    }
    Font8x8_PrintColourCanvas("F1 CPU  O VISUAL V SHOW  ESC EXIT",canvas,32,192,1);
    if(initial) {
        GraphicCanvas_CopyScreen(Screen_GetpLogicGraphic(),Screen_GetpBack());
        GraphicCanvas_CopyScreen(Screen_GetpPhysicGraphic(),Screen_GetpBack());
    }
    Video_SetPalST(gLanceVisMode>=3?gStereoVisPalette:gLanceVisPalette);
}

/* Stable debug/test boundary: frame has been rendered, audio continues in VBL. */
void LanceVis_FrameDone(void) __attribute__((noinline));
void LanceVis_FrameDone(void) { __asm__ volatile ("" ::: "memory"); }

S16 GodLib_Game_Main(S16 argc,char **argv)
{
    void *mod=0;
    U16 quit=0,i;
    (void)argc;(void)argv;
    GemDos_Super(0);Platform_Init();File_Init();
    if(System_GetMCH()!=MCH_STE && System_GetMCH()!=MCH_MEGASTE) {
        GemDos_Cconws("LanceMod sample requires Atari STE/MegaSTE DMA sound.\r\n");
        goto done;
    }
    mod=LanceMod_Load("LOSTPARO.MOD");
    if(!mod) {
        GemDos_Cconws("Could not load LOSTPARO.MOD\r\n");
        goto done;
    }
    Screen_Init(320,200,eGRAPHIC_COLOURMODE_4PLANE,eSCREEN_SCROLL_NONE);
    if(!gScreenClass.mpMemBase)goto unload;
    DrawScene(1);
    if(!LanceMod_Start(mod,eLANCEMOD_FREQ_25K)) {
        LanceMod_Stop();
        goto screen_done;
    }
    gLanceVisReady=1;
    while(!quit) {
        U32 now;
        Screen_Update();IKBD_Update();
        now=Vbl_GetCounter();
        if(gLanceVisFrames && now-gLanceVisLastVbl>1)gLanceVisMissedVbl+=now-gLanceVisLastVbl-1;
        gLanceVisLastVbl=now;
        while(IKBD_GetKbdBytesWaiting()) {
            U8 key=IKBD_PopKbdByte();
            if(key==eIKBDSCAN_SPACE || key==eIKBDSCAN_ESC)quit=1;
            if(key==eIKBDSCAN_F1) {
                gLanceVisRaster^=1;LanceMod_SetRasterDebug(gLanceVisRaster);
            }
            if(key==eIKBDSCAN_V)gLanceVisEnabled^=1;
            if(key==eIKBDSCAN_O) {
                gLanceVisMode=(gLanceVisMode+1)%5;
                DrawScene(0);
                gLanceVisPageView[0]=gLanceVisPageView[1]=0xffff;
            }
        }
        LanceMod_GetVisualizer(gLanceVisAge);
        for(i=0;i<4;++i)
            gLanceVisLevel[i]=(gLanceVisEnabled && gLanceVisAge[i]<16)?16-gLanceVisAge[i]:0;
        gLanceVisPage=Screen_GetLogicIndex();
        gLanceVisScreen=Screen_GetpLogic();
        {
            U16 view=gLanceVisEnabled?gLanceVisMode+1:0;
            if(gLanceVisPageView[gLanceVisPage]!=view) {
                GraphicCanvas_CopyScreen(Screen_GetpLogicGraphic(),Screen_GetpBack());
                Memory_Clear(sizeof(gLanceVisPrevious[0]),gLanceVisPrevious[gLanceVisPage]);
                Memory_Clear(dMODSCOPE_BYTES,gLanceVisScopePrevious[gLanceVisPage]);
                for(i=0;i<dMODSCOPE_XY_POINTS*2;++i)
                    gLanceVisXYPrevious[gLanceVisPage][i]=0xffff;
                if(view==2)ScopeVis_Init(gLanceVisScreen);
                if(view==4)StereoVis_InitSplit(gLanceVisScreen);
                if(view==5)StereoVis_InitMono(gLanceVisScreen);
                gLanceVisPageView[gLanceVisPage]=view;
            }
            if(view==2) {
                LanceMod_GetOscilloscope(gLanceVisScope);
                ScopeVis_Draw(gLanceVisScreen,gLanceVisScope,gLanceVisScopePrevious[gLanceVisPage]);
            } else if(view==3) {
                LanceMod_GetStereoOscilloscope(gLanceVisStereo);
                XYVis_Draw(gLanceVisScreen,gLanceVisStereo,gLanceVisXYPrevious[gLanceVisPage]);
            } else if(view>=4) {
                LanceMod_GetStereoOscilloscope(gLanceVisStereo);
                if(view==4)StereoVis_DrawSplit(gLanceVisScreen,gLanceVisStereo,gLanceVisScopePrevious[gLanceVisPage]);
                else StereoVis_DrawMono(gLanceVisScreen,gLanceVisStereo,gLanceVisScopePrevious[gLanceVisPage]);
            } else if(view==1) {
                LanceVis_Draw(gLanceVisScreen,gLanceVisLevel,gLanceVisPrevious[gLanceVisPage]);
            }
        }
        ++gLanceVisFrames;
        LanceVis_FrameDone();
    }
    LanceMod_StopVbl();
screen_done:
    LanceMod_ShutdownPaula();
    Screen_DeInit();
unload:
    LanceMod_UnLoad(mod);
done:
    File_DeInit();Platform_DeInit();gLanceVisExited=1;
    return 0;
}
