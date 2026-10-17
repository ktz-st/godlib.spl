#include <godlib/gemdos/gemdos.h>
#include <godlib/graphic/graphic.h>
#include <godlib/font8x8/font8x8.h>
#include <godlib/ikbd/ikbd.h>
#include <godlib/memory/memory.h>
#include <godlib/platform/platform.h>
#include <godlib/screen/screen.h>
#include <godlib/vbl/vbl.h>
#include <godlib/video/video.h>
typedef struct { U32 offset;U16 height,words; } sDirty;
extern U8 Lens_Image[];extern U16 Lens_Palette[];extern S16 Lens_Sine[];
extern void Lens_Render(void),Fx_RasterSync(const void *screen);
sDirty gFxOld[2],*gFxDirty;
U8 *gFxScreen,*gFxBackground;
extern void Lens_Init(void);
volatile S16 gFxX=160,gFxY=100;
volatile U16 gFxAuto,gFxPhase,gFxRaster,gFxReady,gFxExited;
volatile U32 gFxFrames,gFxLastVbl,gFxMissedVbl;
void Lens_Record(void) __attribute__((noinline));
void Lens_Record(void)
{
    S16 x1=gFxX-32,x2=gFxX+31,y1=gFxY-32;
    gFxDirty->offset=(U32)y1*160+(x1>>4)*8;
    gFxDirty->words=(x2>>4)-(x1>>4)+1;gFxDirty->height=64;
}
void Lens_RecordEnd(void) {}
S16 GodLib_Game_Main(S16 argc,char **argv)
{
    U16 quit=0;sGraphicCanvas *c;(void)argc;(void)argv;GemDos_Super(0);Platform_Init();
    Screen_Init(320,200,eGRAPHIC_COLOURMODE_4PLANE,0);
    if(!gScreenClass.mpMemBase){Platform_DeInit();return 1;}
    c=Screen_GetpBackGraphic();Memory_Copy(32000,Lens_Image,Screen_GetpBack());
    Font8x8_PrintColourCanvas("GODLIB / MOUSE LENS",c,80,8,15);
    Font8x8_PrintColourCanvas("M MOUSE  A AUTO  R CPU  ESC EXIT",c,32,184,15);
    GraphicCanvas_CopyScreen(Screen_GetpLogicGraphic(),Screen_GetpBack());
    GraphicCanvas_CopyScreen(Screen_GetpPhysicGraphic(),Screen_GetpBack());
    gFxBackground=(U8*)Screen_GetpBack();Lens_Init();
    Video_SetPalST(Lens_Palette);IKBD_EnableMouse();IKBD_SetMousePosition(160,100);gFxReady=1;
    while(!quit) {
        U32 now;Screen_Update();now=Vbl_GetCounter();
        if(gFxFrames && now-gFxLastVbl>1)gFxMissedVbl+=now-gFxLastVbl-1;
        gFxLastVbl=now;IKBD_Update();
        while(IKBD_GetKbdBytesWaiting()) {
            U8 k=IKBD_PopKbdByte();
            if(k==eIKBDSCAN_ESC)quit=1;
            if(k==eIKBDSCAN_R)gFxRaster^=1;
            if(k==eIKBDSCAN_A)gFxAuto=1;
            if(k==eIKBDSCAN_M){gFxAuto=0;IKBD_SetMousePosition(gFxX,gFxY);}
        }
        if(gFxAuto) {
            gFxPhase=(gFxPhase+1)&255;
            gFxX=160+((S32)Lens_Sine[gFxPhase]*112>>7);
            gFxY=100+((S32)Lens_Sine[(gFxPhase*3)&255]*60>>7);
        } else {
            gFxX=IKBD_GetMouseX();gFxY=IKBD_GetMouseY();
            if(gFxX<32)gFxX=32;
            if(gFxX>287)gFxX=287;
            if(gFxY<32)gFxY=32;
            if(gFxY>167)gFxY=167;
            IKBD_SetMousePosition(gFxX,gFxY);
        }
        gFxScreen=(U8*)Screen_GetpLogic();gFxDirty=&gFxOld[Screen_GetLogicIndex()];
        if(gFxRaster){Fx_RasterSync(Screen_GetpPhysic());*(volatile U16*)0xffff8240UL=0x070;}
        Lens_Render();
        if(gFxRaster)*(volatile U16*)0xffff8240UL=Lens_Palette[0];
        Lens_Record();++gFxFrames;
    }
    Screen_DeInit();Platform_DeInit();gFxExited=1;return 0;
}
