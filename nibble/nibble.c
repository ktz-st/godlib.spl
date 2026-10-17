#include <godlib/gemdos/gemdos.h>
#include <godlib/graphic/graphic.h>
#include <godlib/font8x8/font8x8.h>
#include <godlib/ikbd/ikbd.h>
#include <godlib/platform/platform.h>
#include <godlib/screen/screen.h>
#include <godlib/vbl/vbl.h>
#include <godlib/video/video.h>
extern void Nibble_Advance(void),Nibble_Draw(void),Nibble_DrawFlat(void),Nibble_Clear(void);
extern U8 Nibble_Waves[],Nibble_Text[];
U8 *gNibbleScreen,*gNibbleWaveData,*gNibbleText=(U8*)Nibble_Text;
U16 gNibbleGlyph[32],gNibbleBuffer[300];
volatile U16 gNibbleReady,gNibbleExited,gNibblePaused,gNibbleRaster;
volatile U16 gNibblePhase,gNibbleWave,gNibbleCount=1;
volatile U16 gNibbleFramePhase,gNibbleFrameWave;
volatile U32 gNibbleFrames,gNibbleLastVbl,gNibbleMissedVbl;
static U16 gPageWave[2]={65535,65535};
static void Prepare(void)
{
    static U16 pal[16]={0x001,0x777,0x012,0x776,0x023,0x677,0x034,0x757,
                       0x045,0x777,0x056,0x777,0x067,0x777,0x077,0x777};
    sGraphicCanvas *c=Screen_GetpBackGraphic();sGraphicRect r;U16 i;
    GraphicCanvas_ClearScreen(c);
    Font8x8_PrintColourCanvas("G O D L I B",c,120,16,1);
    Font8x8_PrintColourCanvas("THE LOST BOYS - NIBBLE SCROLL",c,48,36,1);
    Font8x8_PrintColourCanvas("68000 ASM / 2 PIXELS PER FRAME",c,40,52,6);
    /* Static even colours leave plane zero for the ASM scroller alone. */
    r.mX=0;r.mWidth=320;r.mHeight=14;
    for(i=0;i<4;++i){r.mY=80+i*14;GraphicCanvas_DrawBox(c,&r,2+i*2);}
    r.mHeight=1;r.mY=70;GraphicCanvas_DrawBox(c,&r,4);
    r.mY=146;GraphicCanvas_DrawBox(c,&r,4);
    Font8x8_PrintColourCanvas("1/2 WAVE  3 FLAT  SPACE PAUSE",c,48,160,6);
    Font8x8_PrintColourCanvas("R CPU   ESC EXIT",c,96,184,1);
    GraphicCanvas_CopyScreen(Screen_GetpLogicGraphic(),Screen_GetpBack());
    GraphicCanvas_CopyScreen(Screen_GetpPhysicGraphic(),Screen_GetpBack());
    Video_SetPalST(pal);
    /* Populate the 320-pixel conveyor before the first visible frame. */
    for(i=0;i<160;++i)Nibble_Advance();
}
S16 GodLib_Game_Main(S16 argc,char **argv)
{
    U16 quit=0;U32 last=0;
    (void)argc;(void)argv;GemDos_Super(0);Platform_Init();
    Screen_Init(320,200,eGRAPHIC_COLOURMODE_4PLANE,0);
    if(!gScreenClass.mpMemBase){Platform_DeInit();return 1;}
    Prepare();gNibbleReady=1;
    while(!quit) {
        U16 page;U32 now;
        Screen_Update();now=Vbl_GetCounter();
        if(last && now-last>1)gNibbleMissedVbl+=now-last-1;
        last=now;gNibbleLastVbl=now;IKBD_Update();
        while(IKBD_GetKbdBytesWaiting()) {
            U8 k=IKBD_PopKbdByte();
            if(k==eIKBDSCAN_ESC)quit=1;
            if(k==eIKBDSCAN_SPACE)gNibblePaused^=1;
            if(k==eIKBDSCAN_R)gNibbleRaster^=1;
            if(k==eIKBDSCAN_1)gNibbleWave=0;
            if(k==eIKBDSCAN_2)gNibbleWave=1;
            if(k==eIKBDSCAN_3)gNibbleWave=2;
        }
        if(gNibbleRaster)*(volatile U16*)0xffff8240UL=0x070;
        if(!gNibblePaused)Nibble_Advance();
        page=Screen_GetLogicIndex();gNibbleScreen=(U8*)Screen_GetpLogic();
        gNibbleWaveData=Nibble_Waves+(gNibbleWave?640:0);
        gNibbleFrameWave=gNibbleWave;gNibbleFramePhase=gNibblePhase;
        /* Original edge clearing assumes continuous movement of one waveform.
           A waveform switch first removes all old plane-zero text on each page. */
        if(gPageWave[page]!=gNibbleWave){Nibble_Clear();gPageWave[page]=gNibbleWave;}
        if(gNibbleWave==2)Nibble_DrawFlat();else Nibble_Draw();
        if(gNibbleRaster)*(volatile U16*)0xffff8240UL=0x001;
        ++gNibbleFrames;
    }
    Screen_DeInit();Platform_DeInit();gNibbleExited=1;return 0;
}
