#include <godlib/gemdos/gemdos.h>
#include <godlib/graphic/graphic.h>
#include <godlib/font8x8/font8x8.h>
#include <godlib/ikbd/ikbd.h>
#include <godlib/platform/platform.h>
#include <godlib/screen/screen.h>
#include <godlib/vbl/vbl.h>
#include <godlib/video/video.h>
extern void PlaneMix_Draw(void),Fx_RasterSync(const void *screen);
U8 *gFxScreen;
volatile U16 gFxAX,gFxAY,gFxBX,gFxBY,gFxPaused,gFxFreezeA,gFxFreezeB,gFxPalette,gFxRaster;
volatile U16 gFxReady,gFxExited;
volatile U32 gFxFrames,gFxLastVbl,gFxMissedVbl;
static void Palette(void)
{
    U16 i,pal[16];for(i=0;i<16;++i)pal[i]=0x777;
    pal[0]=0x001;pal[1]=0x600;pal[2]=0x006;pal[3]=gFxPalette?0x303:0x606;
    Video_SetPalST(pal);
}
S16 GodLib_Game_Main(S16 argc,char **argv)
{
    U16 quit=0;sGraphicCanvas *c;(void)argc;(void)argv;GemDos_Super(0);Platform_Init();
    Screen_Init(320,200,eGRAPHIC_COLOURMODE_4PLANE,0);
    if(!gScreenClass.mpMemBase){Platform_DeInit();return 1;}
    c=Screen_GetpBackGraphic();GraphicCanvas_ClearScreen(c);
    Font8x8_PrintColourCanvas("GODLIB / TRANSPARENT CHECKERS",c,48,16,15);
    Font8x8_PrintColourCanvas("1/2 FREEZE LAYER   SPACE PAUSE",c,40,176,15);
    Font8x8_PrintColourCanvas("P MIX PALETTE  R CPU  ESC EXIT",c,40,192,15);
    GraphicCanvas_CopyScreen(Screen_GetpLogicGraphic(),Screen_GetpBack());
    GraphicCanvas_CopyScreen(Screen_GetpPhysicGraphic(),Screen_GetpBack());Palette();gFxReady=1;
    while(!quit) {
        U32 now;Screen_Update();now=Vbl_GetCounter();
        if(gFxFrames && now-gFxLastVbl>1)gFxMissedVbl+=now-gFxLastVbl-1;
        gFxLastVbl=now;IKBD_Update();
        while(IKBD_GetKbdBytesWaiting()) {
            U8 k=IKBD_PopKbdByte();
            if(k==eIKBDSCAN_ESC)quit=1;
            if(k==eIKBDSCAN_SPACE)gFxPaused^=1;
            if(k==eIKBDSCAN_1)gFxFreezeA^=1;
            if(k==eIKBDSCAN_2)gFxFreezeB^=1;
            if(k==eIKBDSCAN_R)gFxRaster^=1;
            if(k==eIKBDSCAN_P){gFxPalette^=1;Palette();}
        }
        if(!gFxPaused) {
            if(!gFxFreezeA){gFxAX=(gFxAX+1)&31;gFxAY=(gFxAY+1)&31;}
            if(!gFxFreezeB){gFxBX=(gFxBX-1)&15;gFxBY=(gFxBY+2)&15;}
        }
        gFxScreen=(U8*)Screen_GetpLogic();
        if(gFxRaster){Fx_RasterSync(Screen_GetpPhysic());*(volatile U16*)0xffff8240UL=0x070;}
        PlaneMix_Draw();
        if(gFxRaster)*(volatile U16*)0xffff8240UL=0x001;
        ++gFxFrames;
    }
    Screen_DeInit();Platform_DeInit();gFxExited=1;return 0;
}
