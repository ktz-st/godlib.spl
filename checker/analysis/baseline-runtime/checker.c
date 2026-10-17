#include <godlib/gemdos/gemdos.h>
#include <godlib/graphic/graphic.h>
#include <godlib/font8x8/font8x8.h>
#include <godlib/ikbd/ikbd.h>
#include <godlib/platform/platform.h>
#include <godlib/screen/screen.h>
#include <godlib/vbl/vbl.h>
#include <godlib/video/video.h>
typedef struct { S32 first,step,spacing; U16 colour; } sStripe;
typedef struct { U16 colour,edges[23]; } sRow;
extern const sStripe Checker_Params[256][2];
extern void Checker_Draw(void);
extern void Tiny_RasterSync(void *screen);
sRow gCheckerRows[112];
U8 *gCheckerScreen;
volatile U16 gCheckerPhase,gCheckerFramePhase,gCheckerPaused,gCheckerRaster;
volatile U16 gCheckerReady,gCheckerExited,gCheckerSpeed=1;
volatile S16 gCheckerDirection=1;
volatile U32 gCheckerFrames,gCheckerLastVbl,gCheckerMissedVbl;
/* Geometry commands only. The ASM kernel constructs every raster word. */
void Checker_Prepare(void)
{
    const sStripe *p=Checker_Params[gCheckerPhase];
    S32 firstA=p[0].first,firstB=p[1].first;
    U16 colourA=p[0].colour,colourB=p[1].colour,y;
    for(y=0;y<112;++y) {
        U16 n=0;S32 a=firstA,b=firstB;
        gCheckerRows[y].colour=colourA^colourB;
        while(a<81920L || b<81920L) {
            S32 edge;U16 x;
            if(a<=b){edge=a;a+=p[0].spacing;}else{edge=b;b+=p[1].spacing;}
            x=(edge+255)>>8;
            if(x>=320)break;
            gCheckerRows[y].edges[n++]=x;
        }
        gCheckerRows[y].edges[n]=320;
        firstA+=p[0].step;firstB+=p[1].step;
        if(firstA<0){firstA+=p[0].spacing;colourA^=65535;}
        else if(firstA>=p[0].spacing){firstA-=p[0].spacing;colourA^=65535;}
        if(firstB<0){firstB+=p[1].spacing;colourB^=65535;}
        else if(firstB>=p[1].spacing){firstB-=p[1].spacing;colourB^=65535;}
    }
}
void Checker_PrepareEnd(void) {}
static void PrepareScreen(void)
{
    static U16 pal[16]={0x001,0x777,0x012,0x123,0x123,0x345,0x234,0x567,
                               0x345,0x677,0x456,0x777,0x777,0x777,0x777,0x777};
    U16 y;sGraphicRect r={0,48,320,1};sGraphicCanvas *c=Screen_GetpBackGraphic();
    GraphicCanvas_ClearScreen(c);
    Font8x8_PrintColourCanvas("GODLIB / ROTATING CHECKERBOARD",c,40,16,1);
    Font8x8_PrintColourCanvas("SPACE PAUSE   1/2/3 SPEED",c,64,176,1);
    Font8x8_PrintColourCanvas("D REVERSE   R CPU   ESC EXIT",c,48,192,1);
    for(y=0;y<112;++y){r.mY=48+y;GraphicCanvas_DrawBox(c,&r,2+2*(y/28));}
    GraphicCanvas_CopyScreen(Screen_GetpLogicGraphic(),Screen_GetpBack());
    GraphicCanvas_CopyScreen(Screen_GetpPhysicGraphic(),Screen_GetpBack());Video_SetPalST(pal);
}
S16 GodLib_Game_Main(S16 argc,char **argv)
{
    U16 quit=0;(void)argc;(void)argv;GemDos_Super(0);Platform_Init();
    Screen_Init(320,200,eGRAPHIC_COLOURMODE_4PLANE,0);
    if(!gScreenClass.mpMemBase){Platform_DeInit();return 1;}
    PrepareScreen();gCheckerReady=1;
    while(!quit) {
        U32 now;Screen_Update();now=Vbl_GetCounter();
        if(gCheckerFrames && now-gCheckerLastVbl>1)gCheckerMissedVbl+=now-gCheckerLastVbl-1;
        gCheckerLastVbl=now;IKBD_Update();
        while(IKBD_GetKbdBytesWaiting()) {
            U8 k=IKBD_PopKbdByte();
            if(k==eIKBDSCAN_ESC)quit=1;
            if(k==eIKBDSCAN_SPACE)gCheckerPaused^=1;
            if(k==eIKBDSCAN_R)gCheckerRaster^=1;
            if(k==eIKBDSCAN_D)gCheckerDirection=-gCheckerDirection;
            if(k>=eIKBDSCAN_1 && k<=eIKBDSCAN_3)gCheckerSpeed=1<<(k-eIKBDSCAN_1);
        }
        if(!gCheckerPaused)gCheckerPhase=(gCheckerPhase+gCheckerDirection*gCheckerSpeed)&255;
        gCheckerFramePhase=gCheckerPhase;gCheckerScreen=(U8*)Screen_GetpLogic();
        if(gCheckerRaster){Tiny_RasterSync(Screen_GetpPhysic());*(volatile U16*)0xffff8240UL=0x070;}
        Checker_Prepare();Checker_Draw();
        if(gCheckerRaster)*(volatile U16*)0xffff8240UL=0x001;
        ++gCheckerFrames;
    }
    Screen_DeInit();Platform_DeInit();gCheckerExited=1;return 0;
}
