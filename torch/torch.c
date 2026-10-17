#include <godlib/gemdos/gemdos.h>
#include <godlib/graphic/graphic.h>
#include <godlib/font8x8/font8x8.h>
#include <godlib/ikbd/ikbd.h>
#include <godlib/memory/memory.h>
#include <godlib/platform/platform.h>
#include <godlib/screen/screen.h>
#include <godlib/vbl/vbl.h>
#include <godlib/video/video.h>
typedef struct { U32 endOffset;U16 height,words; } sDirty;
extern U8 Torch_Image[];extern U16 Torch_Palette[];extern S16 Torch_Sine[];
extern void Torch_Render(void),Fx_RasterSync(const void *screen);
sDirty gFxOld[2],*gFxDirty;
U8 *gFxScreen;
volatile S16 gFxX=160,gFxY=100;
volatile U16 gFxAuto,gFxPhase,gFxRaster,gFxReady,gFxExited;
volatile U32 gFxFrames,gFxLastVbl,gFxMissedVbl;
void Torch_Record(void) __attribute__((noinline));
void Torch_Record(void)
{
    S16 x1=gFxX-48,x2=gFxX+48,y1=gFxY-48,y2=gFxY+48;
    if(x1<0)x1=0;
    if(x2>319)x2=319;
    if(y1<0)y1=0;
    if(y2>199)y2=199;
    gFxDirty->endOffset=(U32)y1*160+((x2>>4)+1)*8+6;
    gFxDirty->words=(x2>>4)-(x1>>4)+1;gFxDirty->height=y2-y1+1;
}
void Torch_RecordEnd(void) {}
S16 GodLib_Game_Main(S16 argc,char **argv)
{
    U16 quit=0;sGraphicCanvas *c;(void)argc;(void)argv;GemDos_Super(0);Platform_Init();
    Screen_Init(320,200,eGRAPHIC_COLOURMODE_4PLANE,0);
    if(!gScreenClass.mpMemBase){Platform_DeInit();return 1;}
    c=Screen_GetpBackGraphic();Memory_Copy(32000,Torch_Image,Screen_GetpBack());
    Font8x8_PrintColourCanvas("GODLIB / MOUSE TORCH",c,80,8,7);
    Font8x8_PrintColourCanvas("M MOUSE  A AUTO  R CPU  ESC EXIT",c,32,184,7);
    GraphicCanvas_CopyScreen(Screen_GetpLogicGraphic(),Screen_GetpBack());
    GraphicCanvas_CopyScreen(Screen_GetpPhysicGraphic(),Screen_GetpBack());
    Video_SetPalST(Torch_Palette);IKBD_EnableMouse();IKBD_SetMousePosition(160,100);gFxReady=1;
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
            gFxX=160+((S32)Torch_Sine[gFxPhase]*112>>7);
            gFxY=100+((S32)Torch_Sine[(gFxPhase*3)&255]*60>>7);
        } else {
            gFxX=IKBD_GetMouseX();gFxY=IKBD_GetMouseY();
            if(gFxX<0)gFxX=0;
            if(gFxX>319)gFxX=319;
            if(gFxY<0)gFxY=0;
            if(gFxY>199)gFxY=199;
            IKBD_SetMousePosition(gFxX,gFxY);
        }
        gFxScreen=(U8*)Screen_GetpLogic();gFxDirty=&gFxOld[Screen_GetLogicIndex()];
        if(gFxRaster){Fx_RasterSync(Screen_GetpPhysic());*(volatile U16*)0xffff8240UL=0x070;}
        Torch_Render();
        if(gFxRaster)*(volatile U16*)0xffff8240UL=Torch_Palette[0];
        Torch_Record();++gFxFrames;
    }
    Screen_DeInit();Platform_DeInit();gFxExited=1;return 0;
}
