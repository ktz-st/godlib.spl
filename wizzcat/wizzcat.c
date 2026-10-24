/*************************************************************************************
 * GodLib Wizzcat sample: channel activity with James Boulton's STF_DEMO VU bars.
 * Wizzcat_GetVisualizer counts retrigger age; these bars do not measure audio amplitude.
 ************************************************************************************/
#include "../lancemod/dckvis.h"
#include <godlib/string/string.h>
#include <godlib/file/file.h>
#include <godlib/font8x8/font8x8.h>
#include <godlib/gemdos/gemdos.h>
#include <godlib/ikbd/ikbd.h>
#include <godlib/memory/memory.h>
#include <godlib/music/wizzcat.h>
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
S8 gWizzcatVisScope[dMODSCOPE_BYTES],gWizzcatVisScopePrevious[2][dMODSCOPE_BYTES];
extern void XYVis_Draw(void *screen,const S8 *stereo,U16 *previousOffsets);
S8 gWizzcatVisStereo[dMODSCOPE_STEREO_BYTES];
U16 gWizzcatVisXYPrevious[2][dMODSCOPE_XY_POINTS*2];
volatile U16 gWizzcatVisMode; /* 0..4 existing modes; 5..9 five DCK bar layouts. */
U16 gWizzcatVisPageView[2]={0xffff,0xffff};
U16 gWizzcatVisAge[4],gWizzcatVisLevel[4],gWizzcatVisPrevious[2][4];
volatile U16 gWizzcatVisReady,gWizzcatVisExited,gWizzcatVisEnabled=1,gWizzcatVisRaster;
volatile U32 gWizzcatVisFrames,gWizzcatVisLastVbl,gWizzcatVisMissedVbl;
U16 *gWizzcatVisScreen;
U16 gWizzcatVisPage;

static void DrawScene(U16 initial)
{
    U16 i;
    static const U16 x[4]={48,208,256,96};
    sGraphicCanvas *canvas=Screen_GetpBackGraphic();
    GraphicCanvas_ClearScreen(canvas);
    Font8x8_PrintColourCanvas("WIZZCAT / QUICKIE.MOD / 25KHZ",canvas,40,8,gWizzcatVisMode>=5?15:1);
    if(gWizzcatVisMode>=5) {
        static const char *title[5]={"DCK NARROW 32","DCK NARROW 64","DCK WIDE 64","DCK WIDE 128","DCK HORIZONTAL"};
        const char *name=title[gWizzcatVisMode-5];
        Font8x8_PrintColourCanvas(name,canvas,(40-String_StrLen(name))/2*8,28,15);
        for(i=0;i<4;++i){char label[3]={(i==0 || i==3)?'L':'R',(char)('1'+i),0};
            Font8x8_PrintColourCanvas(label,canvas,gWizzcatVisMode==9?8:(gWizzcatVisMode<7?100:104)+32*i,gWizzcatVisMode==9?58+28*i:176,1<<i);
        }
    } else if(gWizzcatVisMode==3) {
        Font8x8_PrintColourCanvas("LEFT",canvas,144,24,4);
        Font8x8_PrintColourCanvas("RIGHT",canvas,144,108,8);
    } else if(gWizzcatVisMode==4) {
        Font8x8_PrintColourCanvas("MONO (L+R)/2",canvas,112,48,1);
    } else if(gWizzcatVisMode==2) {
        Font8x8_PrintColourCanvas("LEFT XY",canvas,52,48,2);
        Font8x8_PrintColourCanvas("RIGHT XY",canvas,208,48,2);
    } else for(i=0;i<4;++i) {
        char text[6]={(i==0 || i==3)?'L':'R',' ','C','H',(char)('1'+i),0};
        Font8x8_PrintColourCanvas(text,canvas,
            gWizzcatVisMode?((i==0 || i==3)?60:220):x[i]-12,
            (gWizzcatVisMode && i>=2)?108:24,2);
    }
    Font8x8_PrintColourCanvas("F1 CPU  O VISUAL V SHOW  ESC EXIT",canvas,32,192,gWizzcatVisMode>=5?15:1);
    if(initial) {
        GraphicCanvas_CopyScreen(Screen_GetpLogicGraphic(),Screen_GetpBack());
        GraphicCanvas_CopyScreen(Screen_GetpPhysicGraphic(),Screen_GetpBack());
    }
    Video_SetPalST(gWizzcatVisMode>=5?gDckModVisPalette:gWizzcatVisMode>=3?gStereoVisPalette:gLanceVisPalette);
}

/* Stable debug/test boundary: frame has been rendered, native VBL audio continues. */
void WizzcatVis_FrameDone(void) __attribute__((noinline));
void WizzcatVis_FrameDone(void) { __asm__ volatile ("" ::: "memory"); }

S16 GodLib_Game_Main(S16 argc,char **argv)
{
    sWizzcatModule *mod=0;
    U16 quit=0,i;
    (void)argc;(void)argv;
    GemDos_Super(0);Platform_Init();File_Init();
    if(System_GetMCH()!=MCH_STE && System_GetMCH()!=MCH_MEGASTE) {
        GemDos_Cconws("Wizzcat sample requires Atari STE/MegaSTE DMA sound.\r\n");
        goto done;
    }
    mod=Wizzcat_Load("QUICKIE.MOD");
    if(!mod) {
        GemDos_Cconws("Could not load QUICKIE.MOD\r\n");
        goto done;
    }
    Screen_Init(320,200,eGRAPHIC_COLOURMODE_4PLANE,eSCREEN_SCROLL_NONE);
    if(!gScreenClass.mpMemBase)goto unload;
    DrawScene(1);
    if(!Wizzcat_Start(mod)) {
        Wizzcat_Stop();
        goto screen_done;
    }
    gWizzcatVisReady=1;
    while(!quit) {
        U32 now;
        Screen_Update();IKBD_Update();
        now=Vbl_GetCounter();
        if(gWizzcatVisFrames && now-gWizzcatVisLastVbl>1)gWizzcatVisMissedVbl+=now-gWizzcatVisLastVbl-1;
        gWizzcatVisLastVbl=now;
        while(IKBD_GetKbdBytesWaiting()) {
            U8 key=IKBD_PopKbdByte();
            if(key==eIKBDSCAN_SPACE || key==eIKBDSCAN_ESC)quit=1;
            if(key==eIKBDSCAN_F1) {
                gWizzcatVisRaster^=1;Wizzcat_SetRasterDebug(gWizzcatVisRaster);
            }
            if(key==eIKBDSCAN_1)Wizzcat_Jump(1);
            if(key==eIKBDSCAN_2)Wizzcat_Jump(mod->mData[950]);
            if(key==eIKBDSCAN_V)gWizzcatVisEnabled^=1;
            if(key==eIKBDSCAN_O) {
                gWizzcatVisMode=(gWizzcatVisMode+1)%10;
                DrawScene(0);
                gWizzcatVisPageView[0]=gWizzcatVisPageView[1]=0xffff;
            }
        }
        Wizzcat_GetVisualizer(gWizzcatVisAge);
        for(i=0;i<4;++i)
            gWizzcatVisLevel[i]=(gWizzcatVisEnabled && gWizzcatVisAge[i]<16)?16-gWizzcatVisAge[i]:0;
        gWizzcatVisPage=Screen_GetLogicIndex();
        gWizzcatVisScreen=Screen_GetpLogic();
        {
            U16 view=gWizzcatVisEnabled?gWizzcatVisMode+1:0;
            if(gWizzcatVisPageView[gWizzcatVisPage]!=view) {
                GraphicCanvas_CopyScreen(Screen_GetpLogicGraphic(),Screen_GetpBack());
                Memory_Clear(sizeof(gWizzcatVisPrevious[0]),gWizzcatVisPrevious[gWizzcatVisPage]);
                Memory_Clear(dMODSCOPE_BYTES,gWizzcatVisScopePrevious[gWizzcatVisPage]);
                for(i=0;i<dMODSCOPE_XY_POINTS*2;++i)
                    gWizzcatVisXYPrevious[gWizzcatVisPage][i]=0xffff;
                if(view==2)ScopeVis_Init(gWizzcatVisScreen);
                if(view==4)StereoVis_InitSplit(gWizzcatVisScreen);
                if(view==5)StereoVis_InitMono(gWizzcatVisScreen);
                gWizzcatVisPageView[gWizzcatVisPage]=view;
            }
            if(view==2) {
                Wizzcat_GetOscilloscope(gWizzcatVisScope);
                ScopeVis_Draw(gWizzcatVisScreen,gWizzcatVisScope,gWizzcatVisScopePrevious[gWizzcatVisPage]);
            } else if(view==3) {
                Wizzcat_GetStereoOscilloscope(gWizzcatVisStereo);
                XYVis_Draw(gWizzcatVisScreen,gWizzcatVisStereo,gWizzcatVisXYPrevious[gWizzcatVisPage]);
            } else if(view==4 || view==5) {
                Wizzcat_GetStereoOscilloscope(gWizzcatVisStereo);
                if(view==4)StereoVis_DrawSplit(gWizzcatVisScreen,gWizzcatVisStereo,gWizzcatVisScopePrevious[gWizzcatVisPage]);
                else StereoVis_DrawMono(gWizzcatVisScreen,gWizzcatVisStereo,gWizzcatVisScopePrevious[gWizzcatVisPage]);
            } else if(view==1) {
                LanceVis_Draw(gWizzcatVisScreen,gWizzcatVisLevel,gWizzcatVisPrevious[gWizzcatVisPage]);
            } else if(view>=6 && view<=10) {
                gDckModVisDraw[view-6](gWizzcatVisScreen,gWizzcatVisLevel,gWizzcatVisPrevious[gWizzcatVisPage]);
            }
        }
        ++gWizzcatVisFrames;
        WizzcatVis_FrameDone();
    }
    Wizzcat_Stop();
screen_done:
    Wizzcat_StopVbl();
    Screen_DeInit();
unload:
    Wizzcat_UnLoad(mod);
done:
    File_DeInit();Platform_DeInit();gWizzcatVisExited=1;
    return 0;
}
