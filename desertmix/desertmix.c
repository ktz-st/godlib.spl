#include <godlib/audio/desertmix.h>
#include <godlib/font8x8/font8x8.h>
#include <godlib/file/file.h>
#include <godlib/gemdos/gemdos.h>
#include <godlib/ikbd/ikbd.h>
#include <godlib/platform/platform.h>
#include <godlib/screen/screen.h>
#include <godlib/video/video.h>
#include <godlib/vbl/vbl.h>
extern U16 DesertMix_Verify(void);
static S8 *sSample;
static U32 sLength;
static U16 sPalette[16]={0,0x777};
volatile U16 gDesertMixDemoReady;
static U8 sRaster;
static U8 sShown[2][4]={{255,255,255,255},{255,255,255,255}};
S16 GodLib_Game_Main(S16 argc,char **argv)
{
    U8 quit=0;
    U16 i,test;
    S32 size;
    (void)argc;(void)argv;
    GemDos_Super(0);Platform_Init();File_Init();
    test=DesertMix_Verify();
    size=File_GetSize("VOICE.RAW");
    if(size>0 && !(size&3L)) { sSample=File_Load("VOICE.RAW");sLength=(U32)size; }
    Screen_Init(320,200,eGRAPHIC_COLOURMODE_4PLANE,eSCREEN_SCROLL_NONE);
    Video_SetPalST(sPalette);
    gDesertMixDemoReady=!test && sSample && DesertMixer_Init();
    /* Static menu in both buffers: keep drawing cost out of audio comparisons. */
    {
        U16 page;
        for(page=0;page<2;++page) {
            U16 *screen;
            if(page) { Screen_Physic_ClearScreen();screen=Screen_GetpPhysic(); }
            else { Screen_Logic_ClearScreen();screen=Screen_GetpLogic(); }
            Font8x8_Print("Desert gameplay mixer / GodLib",screen,8,8);
            Font8x8_Print("4 layers - 12.5 kHz mono",screen,8,24);
            Font8x8_Print(test?"ASM self-test FAILED":"ASM self-test PASS",screen,8,40);
            Font8x8_Print(gDesertMixDemoReady?"F1/F2: toggle a loop":"Sample or DMA init failed",screen,8,56);
            Font8x8_Print("F3/F4: one-shot / F5: all",screen,8,72);
            Font8x8_Print("F6: stop / F9: CPU raster",screen,8,88);
            Font8x8_Print("ESC: quit",screen,8,104);
        }
    }
    /* Static diagnostics use one displayed page; update only changed fields. */
    Screen_Update();
    while(!quit) {
        U16 *screen;
        Vbl_WaitVbl();screen=Screen_GetpPhysic();
        for(i=0;i<4;++i) {
            U8 active=DesertMixer_IsPlaying(i);
            U16 page=gScreenClass.mPhysicIndex;
            if(sShown[page][i]!=active) {
                char line[]="CH1: STOP";line[2]=(char)('1'+i);
                if(active) {line[5]='P';line[6]='L';line[7]='A';line[8]='Y';}
                Font8x8_Print(line,screen,8,128+i*16);
                sShown[page][i]=active;
            }
        }
        IKBD_Update();
        while(IKBD_GetKbdBytesWaiting()) {
            U8 key=IKBD_PopKbdByte();
            if(key==eIKBDSCAN_ESC) quit=1;
            if(key==eIKBDSCAN_F9) {sRaster^=1;DesertMixer_SetRasterDebug(sRaster);}
            if(!gDesertMixDemoReady) continue;
            if(key>=eIKBDSCAN_F1 && key<=eIKBDSCAN_F4) {
                i=key-eIKBDSCAN_F1;
                if(i<2 && DesertMixer_IsPlaying(i)) DesertMixer_Stop(i);
                else DesertMixer_Play(i,sSample,sLength,i<2);
            }
            if(key==eIKBDSCAN_F5) for(i=0;i<4;++i) DesertMixer_Play(i,sSample,sLength,i<2);
            if(key==eIKBDSCAN_F6) DesertMixer_StopAll();
        }
    }
    DesertMixer_DeInit();
    if(sSample) File_UnLoad(sSample);
    File_DeInit();Screen_DeInit();Platform_DeInit();
    return 0;
}
