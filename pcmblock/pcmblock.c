#include <godlib/audio/pcmblock.h>
#include <godlib/font8x8/font8x8.h>
#include <godlib/file/file.h>
#include <godlib/gemdos/gemdos.h>
#include <godlib/ikbd/ikbd.h>
#include <godlib/platform/platform.h>
#include <godlib/screen/screen.h>
#include <godlib/video/video.h>
#include <godlib/vbl/vbl.h>

extern U16 PcmBlockMix_Verify(void);
static U8 sRaster;
static U8 sShown[2][4]={{255,255,255,255},{255,255,255,255}};
static S8 * sSample[2];
static U32 sLength[2];
static U16 sPalette[16]={0,0x777};
/* Visible in debugger for reproducible validation. */
volatile U16 gPcmBlockMixDemoRate,gPcmBlockMixDemoReady,gPcmBlockMixDemoLoops;

S16 GodLib_Game_Main(S16 argc, char **argv)
{
    U8 quit=0;
    U16 test,i;
    (void)argc; (void)argv;
    GemDos_Super(0);
    Platform_Init();
    File_Init();
    test=PcmBlockMix_Verify();
    for(i=0;i<2;++i) {
        const char * name=i?"VOICE25.RAW":"VOICE12.RAW";
        S32 size=File_GetSize(name);
        if(size>0 && !(size & 511L)) {
            sSample[i]=File_Load(name);
            sLength[i]=(U32)size;
        }
    }
    Screen_Init(320,200,eGRAPHIC_COLOURMODE_4PLANE,eSCREEN_SCROLL_NONE);
    Video_SetPalST(sPalette);
    gPcmBlockMixDemoRate=ePCMBLOCK_FREQ_25K;
    gPcmBlockMixDemoReady=!test && sSample[0] && sSample[1] && PcmBlockMixer_Init(gPcmBlockMixDemoRate);
    /* Static menu in both buffers: keep drawing cost out of audio comparisons. */
    {
        U16 page;
        for(page=0;page<2;++page) {
            U16 *screen;
            if(page) { Screen_Physic_ClearScreen();screen=Screen_GetpPhysic(); }
            else { Screen_Logic_ClearScreen();screen=Screen_GetpLogic(); }
            Font8x8_Print("PCM Block 4-channel mixer / GodLib",screen,8,8);
            Font8x8_Print(gPcmBlockMixDemoRate==ePCMBLOCK_FREQ_25K?"25 kHz mono":"12.5 kHz mono",screen,8,24);
            Font8x8_Print(test?"ASM self-test FAILED":"ASM self-test PASS",screen,8,40);
            Font8x8_Print(gPcmBlockMixDemoReady?"F1-F4: trigger a channel":"Sample or DMA init failed",screen,8,56);
            Font8x8_Print("F5: play all / F6: loop all",screen,8,72);
            Font8x8_Print("F7: stop all / F8: switch rate",screen,8,88);
            Font8x8_Print("F9: CPU raster / ESC: quit",screen,8,104);
        }
    }
    /* Static diagnostics use one displayed page; update only changed fields. */
    Screen_Update();
    while(!quit) {
        U16 * screen;
        Vbl_WaitVbl();
        screen=Screen_GetpPhysic();
        Font8x8_Print(gPcmBlockMixDemoRate==ePCMBLOCK_FREQ_25K?"25 kHz mono  ":"12.5 kHz mono",screen,8,24);
        for(i=0;i<4;++i) {
            U8 active=PcmBlockMixer_IsPlaying(i);
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
            U16 index=gPcmBlockMixDemoRate-1;
            if(key==eIKBDSCAN_F9) { sRaster^=1; PcmBlockMixer_SetRasterDebug(sRaster); }
            if(key==eIKBDSCAN_ESC) quit=1;
            if(!gPcmBlockMixDemoReady) continue;
            if(key>=eIKBDSCAN_F1 && key<=eIKBDSCAN_F4)
                PcmBlockMixer_Play(key-eIKBDSCAN_F1,sSample[index],sLength[index],0);
            if(key==eIKBDSCAN_F5 || key==eIKBDSCAN_F6) {
                gPcmBlockMixDemoLoops=(key==eIKBDSCAN_F6);
                for(i=0;i<4;++i) PcmBlockMixer_Play(i,sSample[index],sLength[index],gPcmBlockMixDemoLoops);
            }
            if(key==eIKBDSCAN_F7) {
                PcmBlockMixer_StopAll();gPcmBlockMixDemoLoops=0;
            }
            if(key==eIKBDSCAN_F8) {
                U16 rate=(gPcmBlockMixDemoRate==ePCMBLOCK_FREQ_25K)?ePCMBLOCK_FREQ_12K:ePCMBLOCK_FREQ_25K;
                if(PcmBlockMixer_SetFrequency(rate)) gPcmBlockMixDemoRate=rate;
                gPcmBlockMixDemoLoops=0;
            }
        }
    }
    PcmBlockMixer_DeInit();
    for(i=0;i<2;++i) if(sSample[i]) File_UnLoad(sSample[i]);
    File_DeInit();
    Screen_DeInit();
    Platform_DeInit();
    return 0;
}
