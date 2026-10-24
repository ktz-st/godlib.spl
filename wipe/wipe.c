/* Three PI1 pictures and GodLib's 39 CPU/BLiTTER wipe effects, on ST/STE. */
#include <godlib/file/file.h>
#include <godlib/font8x8/font8x8.h>
#include <godlib/gemdos/gemdos.h>
#include <godlib/ikbd/ikbd.h>
#include <godlib/pictypes/degas.h>
#include <godlib/platform/platform.h>
#include <godlib/graphic/graphic.h>
#include <godlib/screen/screen.h>
#include <godlib/system/system.h>
#include <godlib/vbl/vbl.h>
#include <godlib/video/video.h>
#include <godlib/wipe/wipe.h>
#include <stdio.h>

#define SLIDES 3
#define SCREEN_BYTES 32000UL
#define HOLD_VBLS 200UL
#define STAGE_IN 0
#define STAGE_HOLD 1
#define STAGE_OUT 2
static const char *sFiles[SLIDES]={"COAST.PI1","SPACE.PI1","FOREST.PI1"};
static const char *sNames[SLIDES]={"COAST","SPACE","FOREST"};
static sDegas *sPictures[SLIDES];
/* ScreenBack is the canonical transition buffer: an in-place wipe-out must
 * see every mask even when the displayed pages alternate. */
static U32 sHoldStart;
static U8 sNext, sPalettePending;
volatile U16 gSlideIndex, gWipeEffect, gWipeStage, gWipeTicks;
volatile U16 gAutoPause, gSlideReady;
volatile U16 gWipeBlitter,gWipeRaster,gWipeExited;
volatile U32 gWipeFrames,gWipeMissedVbl;
U8 *gWipePresented;
static void StartIn(void);
#ifdef WIPE_BENCH
extern const U16 gWipeFrameCounts[39];
extern void WipeBench_Update(U16 *dest);
volatile U16 gWipeBenchHold,gWipeBenchRequest,gWipeBenchDone,gWipeBenchEffect,gWipeBenchClosing,gWipeBenchBackend,gWipeBenchReset,gWipeBenchActual,gWipeBenchFinished,gWipeBenchAbiFailed,gWipeHoldOnBlack,gWipeAtBlack;
volatile U32 gWipeBenchCalls;
U16 gWipeBenchMemory[16020]; /* two guards + pixels, then a four-word result */
U16 *gWipeBenchSource;
static void BenchInit(void)
{
    U16 n;U16 *dest=gWipeBenchMemory+8;gWipeBenchSource=sPictures[0]->mPixels;
    for(n=0;n<8;++n)gWipeBenchMemory[n]=gWipeBenchMemory[16008+n]=0xa55a;
    if(gWipeBenchClosing){
        sGraphicCanvas c=*Screen_GetpBackGraphic();c.mpVRAM=dest;c.mpFuncs->CopyScreen(&c,sPictures[0]->mPixels);
        Wipe_Out_Init(gWipeBenchEffect);
    }else{
        sGraphicCanvas c=*Screen_GetpBackGraphic();c.mpVRAM=dest;c.mpFuncs->ClearScreen(&c);
        Wipe_In_Init(gWipeBenchEffect,sPictures[0]->mPixels);
    }
    gWipeBenchCalls=0;gWipeBenchAbiFailed=0;gWipeBenchReset=0;
}
static void BenchRun(U16 request)
{
    U16 effect,n;U32 total=0;
    Wipe_SetBlitterEnable(gWipeBenchBackend);gWipeBenchActual=Wipe_GetBlitterEnable();
    if(request==4){
        gSlideIndex=0;gWipeEffect=0;gWipeBlitter=gWipeBenchActual;sPalettePending=0;sNext=0;
        GraphicCanvas_ClearScreen(Screen_GetpBackGraphic());Video_SetPalST(sPictures[0]->mHeader.mPalette);StartIn();
    }else if(request==2){
        gWipeBenchCalls=0;
        for(effect=0;effect<39;++effect){
            gWipeBenchEffect=effect;BenchInit();
            for(n=0;n<gWipeFrameCounts[effect];++n){Wipe_Update(gWipeBenchMemory+8);++total;}
        }
        gWipeBenchCalls=total;
    }else{
        if(gWipeBenchReset)BenchInit();
        WipeBench_Update(gWipeBenchMemory+8);++gWipeBenchCalls;
    }
    gWipeBenchFinished=Wipe_IsFinished()!=0;
    gWipeBenchMemory[16016]=gWipeBenchActual;gWipeBenchMemory[16017]=gWipeBenchFinished;
    gWipeBenchMemory[16018]=gWipeBenchAbiFailed;gWipeBenchMemory[16019]=(U16)gWipeBenchCalls;
    gWipeBenchDone=request;
}
#endif

static void StartIn(void)
{
    Wipe_In_Init(gWipeEffect,sPictures[gSlideIndex]->mPixels);
    gWipeStage=STAGE_IN;
}

static void DrawOverlay(void)
{
    char caption[40];
    sprintf(caption,"%s / WIPE %02u/39 / %s",sNames[gSlideIndex],(unsigned int)(gWipeEffect+1),gWipeBlitter?"BLITTER":"CPU");
    Font8x8_PrintColour(caption,Screen_GetpLogic(),0,8,15);
    Font8x8_PrintColour(gAutoPause?"SPACE NEXT  P AUTO ON   B CPU/BLITTER":"SPACE NEXT  P AUTO OFF  B CPU/BLITTER",Screen_GetpLogic(),0,184,15);
    Font8x8_PrintColour("R CPU STRIPE               ESC EXIT",Screen_GetpLogic(),0,192,15);
}

static void UpdateSlide(void)
{
    if(gWipeStage==STAGE_HOLD) {
        if(sNext || (!gAutoPause && Vbl_GetCounter()-sHoldStart>=HOLD_VBLS)) {
            sNext=0;
            Wipe_Out_Init(gWipeEffect);
            gWipeStage=STAGE_OUT;
        }
    }
    if(gWipeStage!=STAGE_HOLD) {
        /* Exactly one state advance per displayed frame; both wipe directions
         * render into the same buffer. Wipe_Update's return value is unused. */
        if(gWipeRaster)*(volatile U16*)0xffff8240UL=0x070;
        Wipe_Update(Screen_GetpBack());
        if(gWipeRaster)*(volatile U16*)0xffff8240UL=0;
        ++gWipeTicks;
        if(Wipe_IsFinished()) {
            if(gWipeStage==STAGE_IN) {
                /* Every final mask is all ones: Back already equals source. */
                sHoldStart=Vbl_GetCounter();
                gWipeStage=STAGE_HOLD;
            }
            else {
                gSlideIndex=(gSlideIndex+1)%SLIDES;
                gWipeEffect=(gWipeEffect+1)%dWIPE_FX_LIMIT;
                StartIn();
                sPalettePending=1;
            }
        }
    }
    Screen_Logic_CopyScreen(Screen_GetpBack());
    DrawOverlay();
    gWipePresented=(U8*)Screen_GetpLogic();
    Screen_Update();
    {static U32 last;U32 now=Vbl_GetCounter();if(last && now-last>2)gWipeMissedVbl+=now-last-2;last=now;++gWipeFrames;}
    /* The wipe-out black frame is now displayed. Change palette only here,
     * before the next image begins to appear. Index 0 is black in every PI1. */
    if(sPalettePending) {
#ifdef WIPE_BENCH
        gWipeAtBlack=1;while(gWipeHoldOnBlack){}gWipeAtBlack=0;
#endif
        Video_SetPalST(sPictures[gSlideIndex]->mHeader.mPalette);
        sPalettePending=0;
    }
}

S16 GodLib_Game_Main(S16 argc,char **argv)
{
    U16 i;
    U8 quit=0, valid=1;
    (void)argc; (void)argv;
    GemDos_Super(0);
    Platform_Init(); File_Init();
    /* Preload all pictures before starting the transitions. */
    for(i=0;i<SLIDES;++i) {
        if(File_GetSize(sFiles[i])!=32034L) { valid=0; break; }
        sPictures[i]=File_Load(sFiles[i]);
        if(!sPictures[i] || sPictures[i]->mHeader.mMode!=0) { valid=0; break; }
        if(sPictures[i]->mHeader.mPalette[0]!=0) { valid=0; break; }
    }
    if(valid) {
        Screen_Init(320,200,eGRAPHIC_COLOURMODE_4PLANE,eSCREEN_SCROLL_NONE);
        if(!gScreenClass.mpMemBase){valid=0;goto unload;}
        Graphic_SetBlitterEnable(0); /* Identical CPU presentation copy for A/B. */
        Wipe_SetBlitterEnable(1);gWipeBlitter=Wipe_GetBlitterEnable();
        Screen_SetFrameRate(2); /* At least two VBLs per wipe step. */
        Video_SetPalST(sPictures[0]->mHeader.mPalette);
#ifdef WIPE_BENCH
        gAutoPause=1; /* deterministic UI tests after the initial wipe */
#endif
        StartIn(); gSlideReady=1;
        while(!quit) {
#ifdef WIPE_BENCH
            if(gWipeBenchHold){if(gWipeBenchRequest){U16 request=gWipeBenchRequest;gWipeBenchRequest=0;BenchRun(request);}continue;}
#endif
            IKBD_Update();
            while(IKBD_GetKbdBytesWaiting()) {
                U8 key=IKBD_PopKbdByte();
                if(key==eIKBDSCAN_ESC) quit=1;
                if(key==eIKBDSCAN_SPACE) sNext=1;
                if(key==eIKBDSCAN_P) { gAutoPause^=1; sHoldStart=Vbl_GetCounter(); }
                if(key==eIKBDSCAN_B) { Wipe_SetBlitterEnable(!gWipeBlitter);gWipeBlitter=Wipe_GetBlitterEnable(); }
                if(key==eIKBDSCAN_R)gWipeRaster^=1;
            }
            if(!quit) UpdateSlide();
        }
        Wipe_SetBlitterEnable(0);Screen_DeInit();
    }
    else printf("Missing/invalid PI1 files. Run WIPE.PRG alongside COAST, SPACE and FOREST.PI1.\n");
unload:
    for(i=0;i<SLIDES;++i) if(sPictures[i]) File_UnLoad(sPictures[i]);
    File_DeInit(); Platform_DeInit();
    gWipeExited=1;
    return valid?0:1;
}
