#include <godlib/audio/slugmix.h>
#include <godlib/font8x8/font8x8.h>
#include <godlib/file/file.h>
#include <godlib/gemdos/gemdos.h>
#include <godlib/ikbd/ikbd.h>
#include <godlib/platform/platform.h>
#include <godlib/screen/screen.h>
#include <godlib/video/video.h>
#include <godlib/vbl/vbl.h>

static U8 sRaster;
static U8 sShown[2][3]={{255,255,255},{255,255,255}};
static S8 * sSample;
static U16 sBlocks;
static U16 sPalette[16] = {0,0x777};

S16 GodLib_Game_Main(S16 argc, char ** argv)
{
    U8 quit=0, loop=0, ready;
    U16 i;
    (void)argc; (void)argv;
    GemDos_Super(0);
    Platform_Init();
    File_Init();
    {
        S32 size=File_GetSize("VOICE.RAW");
        if (size>0 && size<=63750 && size%250==0) {
            sSample=File_Load("VOICE.RAW");
            sBlocks=(U16)(size/250);
        }
    }
    Screen_Init(320,200,eGRAPHIC_COLOURMODE_4PLANE,eSCREEN_SCROLL_NONE);
    Video_SetPalST(sPalette);
    ready=sSample && SlugMixer_Init();
    /* Static menu in both buffers: keep drawing cost out of audio comparisons. */
    {
        U16 page;
        for(page=0;page<2;++page) {
            U16 *screen;
            if(page) { Screen_Physic_ClearScreen();screen=Screen_GetpPhysic(); }
            else { Screen_Logic_ClearScreen();screen=Screen_GetpLogic(); }
            Font8x8_Print("Metal Slug mixer / GodLib",screen,8,8);
            Font8x8_Print("3 channels - 12.5 kHz mono",screen,8,24);
            Font8x8_Print(ready ? "F1/F2/F3: voice on channel 1/2/3" : "Sample or DMA init failed",screen,8,48);
            Font8x8_Print("F4: play all three",screen,8,64);
            Font8x8_Print("F5: toggle channel 2 loop",screen,8,80);
            Font8x8_Print("F6: stop all / ESC: quit",screen,8,96);
            Font8x8_Print("F9: CPU raster",screen,8,112);
        }
    }
    /* Static diagnostics use one displayed page; update only changed fields. */
    Screen_Update();
    while (!quit) {
        U16 * screen;
        Vbl_WaitVbl();
        screen=Screen_GetpPhysic();
        for(i=0;i<3;++i) {
            U8 active=SlugMixer_IsPlaying(i);
            U16 page=gScreenClass.mPhysicIndex;
            if(sShown[page][i]!=active) {
                char line[]="CH1: STOP";line[2]=(char)('1'+i);
                if(active) {line[5]='P';line[6]='L';line[7]='A';line[8]='Y';}
                Font8x8_Print(line,screen,8,128+i*16);
                sShown[page][i]=active;
            }
        }
        IKBD_Update();
        while (IKBD_GetKbdBytesWaiting()) {
            U8 key=IKBD_PopKbdByte();
            U16 j;
            if (key==eIKBDSCAN_F9) { sRaster^=1; SlugMixer_SetRasterDebug(sRaster); }
            if (key==eIKBDSCAN_ESC) quit=1;
            if (!ready) continue;
            if (key>=eIKBDSCAN_F1 && key<=eIKBDSCAN_F3) {
                j=key-eIKBDSCAN_F1;
                SlugMixer_Play(j,sSample,sBlocks,0);
                if (j==1) loop=0;
            }
            if (key==eIKBDSCAN_F4) {
                for (j=0;j<3;++j) SlugMixer_Play(j,sSample,sBlocks,0);
                loop=0;
            }
            if (key==eIKBDSCAN_F5) {
                loop^=1;
                if (loop) SlugMixer_Play(1,sSample,sBlocks,1);
                else SlugMixer_Stop(1);
            }
            if (key==eIKBDSCAN_F6) {
                for (j=0;j<3;++j) SlugMixer_Stop(j);
                loop=0;
            }
        }
    }
    SlugMixer_DeInit();
    if (sSample) File_UnLoad(sSample);
    File_DeInit();
    Screen_DeInit();
    Platform_DeInit();
    return 0;
}
