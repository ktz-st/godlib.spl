/* Three PI1 pictures and GodLib's 39 software wipe effects, on ST/STE. */
#include <godlib/file/file.h>
#include <godlib/font8x8/font8x8.h>
#include <godlib/gemdos/gemdos.h>
#include <godlib/ikbd/ikbd.h>
#include <godlib/pictypes/degas.h>
#include <godlib/platform/platform.h>
#include <godlib/screen/screen.h>
#include <godlib/vbl/vbl.h>
#include <godlib/video/video.h>
#include <godlib/wipe/wipe.h>
#include <stdio.h>
#include <string.h>

#define SLIDES 3
#define SCREEN_BYTES 32000UL
#define HOLD_VBLS 200UL
#define STAGE_IN 0
#define STAGE_HOLD 1
#define STAGE_OUT 2
static const char *sFiles[SLIDES]={"COAST.PI1","SPACE.PI1","FOREST.PI1"};
static const char *sNames[SLIDES]={"COAST","SPACE","FOREST"};
static sDegas *sPictures[SLIDES];
/* Wipe-out modifies its destination in place. Keep one canonical transition
 * buffer so alternating logical screens never miss an intermediate mask. */
static U16 sTransition[16000];
static U32 sHoldStart;
static U8 sNext, sPalettePending;
volatile U16 gSlideIndex, gWipeEffect, gWipeStage, gWipeTicks;
volatile U16 gAutoPause, gSlideReady;

static void StartIn(void)
{
    Wipe_In_Init(gWipeEffect,sPictures[gSlideIndex]->mPixels);
    gWipeStage=STAGE_IN;
}

static void DrawOverlay(void)
{
    char caption[40];
    sprintf(caption,"%s / WIPE %02u OF 39",sNames[gSlideIndex],(unsigned int)(gWipeEffect+1));
    Font8x8_PrintColour(caption,Screen_GetpLogic(),8,8,15);
    Font8x8_PrintColour(gAutoPause?"SPACE: next  P: auto on  ESC: exit":"SPACE: next  P: pause    ESC: exit",
        Screen_GetpLogic(),8,184,15);
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
        Wipe_Update(sTransition);
        ++gWipeTicks;
        if(Wipe_IsFinished()) {
            if(gWipeStage==STAGE_IN) {
                /* Ensure the holding frame is the complete source picture. */
                memcpy(sTransition,sPictures[gSlideIndex]->mPixels,SCREEN_BYTES);
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
    memcpy(Screen_GetpLogic(),sTransition,SCREEN_BYTES);
    DrawOverlay();
    Screen_Update();
    /* The wipe-out black frame is now displayed. Change palette only here,
     * before the next image begins to appear. Index 0 is black in every PI1. */
    if(sPalettePending) {
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
        Screen_SetFrameRate(2); /* At least two VBLs per wipe step. */
        Video_SetPalST(sPictures[0]->mHeader.mPalette);
        StartIn(); gSlideReady=1;
        while(!quit) {
            IKBD_Update();
            while(IKBD_GetKbdBytesWaiting()) {
                U8 key=IKBD_PopKbdByte();
                if(key==eIKBDSCAN_ESC) quit=1;
                if(key==eIKBDSCAN_SPACE) sNext=1;
                if(key==eIKBDSCAN_P) { gAutoPause^=1; sHoldStart=Vbl_GetCounter(); }
            }
            if(!quit) UpdateSlide();
        }
        Screen_DeInit();
    }
    else printf("Missing/invalid PI1 files. Run WIPE.TOS alongside COAST, SPACE and FOREST.PI1.\n");
    for(i=0;i<SLIDES;++i) if(sPictures[i]) File_UnLoad(sPictures[i]);
    File_DeInit(); Platform_DeInit();
    return valid?0:1;
}
