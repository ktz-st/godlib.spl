/*************************************************************************************
 * GodLib Leonard sample: channel activity with James Boulton's STF_DEMO VU bars.
 * mt_Visualizer counts retrigger age; these bars do not measure audio amplitude.
 ************************************************************************************/
#include "../lancemod/dckvis.h"
#include <godlib/string/string.h>
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
volatile U16 gLeonardVisMode; /* 0..4 existing modes; 5..9 five DCK bar layouts. */
U16 gLeonardVisPageView[2]={0xffff,0xffff};
U16 gLeonardVisAge[4],gLeonardVisLevel[4],gLeonardVisPrevious[2][4];
volatile U16 gLeonardVisReady,gLeonardVisExited,gLeonardVisEnabled=1,gLeonardVisRaster;
volatile U32 gLeonardVisFrames,gLeonardVisLastVbl,gLeonardVisMissedVbl;
volatile U32 gLeonardVisAudioTicks;
volatile U16 gLeonardVisAudioAttached,gLeonardVisAudioDetached;

/* One owner, independent of rendering. Tick preserves USP/SR like UGH's
 * VBL service; do not also call it from the foreground loop. */
void LeonardVis_AudioVbl(void)
{
    LeonardMod_Tick();
    ++gLeonardVisAudioTicks;
}
U16 *gLeonardVisScreen;
U16 gLeonardVisPage;

static void DrawScene(U16 initial)
{
    U16 i;
    static const U16 x[4]={48,208,256,96};
    sGraphicCanvas *canvas=Screen_GetpBackGraphic();
    GraphicCanvas_ClearScreen(canvas);
    Font8x8_PrintColourCanvas(LEONARD_RATE==eLEONARDMOD_FREQ_12K?
        "LEONARD / LOSTPARO.MOD / 12.5KHZ":"LEONARD / LOSTPARO.MOD / 25KHZ",canvas,32,8,gLeonardVisMode>=5?15:1);
    if(gLeonardVisMode>=5) {
        static const char *title[5]={"DCK NARROW 32","DCK NARROW 64","DCK WIDE 64","DCK WIDE 128","DCK HORIZONTAL"};
        const char *name=title[gLeonardVisMode-5];
        Font8x8_PrintColourCanvas(name,canvas,(40-String_StrLen(name))/2*8,28,15);
        for(i=0;i<4;++i){char label[3]={(i==0 || i==3)?'L':'R',(char)('1'+i),0};
            Font8x8_PrintColourCanvas(label,canvas,gLeonardVisMode==9?8:(gLeonardVisMode<7?100:104)+32*i,gLeonardVisMode==9?58+28*i:176,1<<i);
        }
    } else if(gLeonardVisMode==3) {
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
    Font8x8_PrintColourCanvas("F1 CPU  O VISUAL V SHOW  ESC EXIT",canvas,32,192,gLeonardVisMode>=5?15:1);
    if(initial) {
        GraphicCanvas_CopyScreen(Screen_GetpLogicGraphic(),Screen_GetpBack());
        GraphicCanvas_CopyScreen(Screen_GetpPhysicGraphic(),Screen_GetpBack());
    }
    Video_SetPalST(gLeonardVisMode>=5?gDckModVisPalette:gLeonardVisMode>=3?gStereoVisPalette:gLanceVisPalette);
}

/* Stable debug/test boundary: frame rendered; audio has its own VBL owner. */
void LeonardVis_FrameDone(void) __attribute__((noinline));
void LeonardVis_FrameDone(void) { __asm__ volatile ("" ::: "memory"); }

S16 GodLib_Game_Main(S16 argc,char **argv)
{
    void *mod=0;
    U16 quit=0,i,mask;
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
    mask=System_GetIML();System_SetIML(7);
    gLeonardVisAudioAttached=Vbl_AddCall(LeonardVis_AudioVbl);
    System_SetIML(mask);
    if(!gLeonardVisAudioAttached)goto screen_done;
    gLeonardVisReady=1;
    while(!quit) {
        U32 now;
        Screen_Update();IKBD_Update();
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
                gLeonardVisMode=(gLeonardVisMode+1)%10;
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
            } else if(view==4 || view==5) {
                LeonardMod_GetStereoOscilloscope(gLeonardVisStereo);
                if(view==4)StereoVis_DrawSplit(gLeonardVisScreen,gLeonardVisStereo,gLeonardVisScopePrevious[gLeonardVisPage]);
                else StereoVis_DrawMono(gLeonardVisScreen,gLeonardVisStereo,gLeonardVisScopePrevious[gLeonardVisPage]);
            } else if(view==1) {
                LanceVis_Draw(gLeonardVisScreen,gLeonardVisLevel,gLeonardVisPrevious[gLeonardVisPage]);
            } else if(view>=6 && view<=10) {
                gDckModVisDraw[view-6](gLeonardVisScreen,gLeonardVisLevel,gLeonardVisPrevious[gLeonardVisPage]);
            }
        }
        ++gLeonardVisFrames;
        LeonardVis_FrameDone();
    }
screen_done:
    /* Remove the callback before stopping DMA/trap #0 or freeing MOD/workspace. */
    mask=System_GetIML();System_SetIML(7);
    if(gLeonardVisAudioAttached) {
        Vbl_RemoveCall(LeonardVis_AudioVbl);
        gLeonardVisAudioAttached=0;
    }
    gLeonardVisAudioDetached=1;
    System_SetIML(mask);
    LeonardMod_ShutdownPaula();
    Screen_DeInit();
unload:
    LeonardMod_UnLoad(mod);
done:
    File_DeInit();Platform_DeInit();gLeonardVisExited=1;
    return 0;
}
