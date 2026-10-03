/* Draw byte-per-pixel indices, then convert them to an ST-low screen. */
#include <godlib/chunky/chunky.h>
#include <godlib/font8x8/font8x8.h>
#include <godlib/gemdos/gemdos.h>
#include <godlib/ikbd/ikbd.h>
#include <godlib/platform/platform.h>
#include <godlib/screen/screen.h>
#include <godlib/video/video.h>
#include <string.h>

#define WIDTH 256
#define HEIGHT 128
/* U16 storage guarantees even alignment for the assembler's longword reads.
 * Each pixel is still one U8 palette index (0..15), not a packed nibble. */
static U16 sPixels[(U32)WIDTH * HEIGHT / 2];
static U16 sBackground[(U32)WIDTH * HEIGHT / 2];
static sGraphicCanvas sChunky;
static U16 sPalette[16] = {
    0x000,0x112,0x223,0x334,0x445,0x556,0x667,0x777,
    0x700,0x730,0x770,0x070,0x077,0x007,0x707,0x777
};
static S16 sX=12, sY=40, sStepX=2, sStepY=1;
static U8 sPaused;
volatile U16 gChunkyDemoFrames;

static void DrawChunky(void)
{
    sGraphicRect box;
    sGraphicBox line;
    /* Restore the byte-per-pixel checkerboard and palette strip. */
    memcpy(sPixels,sBackground,sizeof(sPixels));
    box.mX=sX; box.mY=sY; box.mWidth=48; box.mHeight=24;
    ChunkySurface_DrawBox(&sChunky,&box,8);
    box.mX+=4; box.mY+=4; box.mWidth-=8; box.mHeight-=8;
    ChunkySurface_DrawBox(&sChunky,&box,10);
    line.mX0=0; line.mY0=127; line.mX1=sX+24; line.mY1=sY+12;
    ChunkySurface_DrawLine(&sChunky,&line,12);
    line.mX0=255; line.mY0=127;
    ChunkySurface_DrawLine(&sChunky,&line,14);
    if(!sPaused) {
        sX+=sStepX; sY+=sStepY;
        if(sX<=0 || sX>=WIDTH-48) sStepX=-sStepX;
        if(sY<=28 || sY>=HEIGHT-24) sStepY=-sStepY;
    }
}

static void DrawFrame(void)
{
    sGraphicRect source={0,0,WIDTH,HEIGHT};
    sGraphicPos destination={32,56};
    DrawChunky();
    Screen_Logic_ClearScreen();
    /* This is the actual chunky -> planar conversion, into the next screen.
     * The source is 256 bytes/row; the destination screen is 160 bytes/row.
     * The wrapper gets both strides from their respective canvases. */
    ChunkySurface_To4Plane(Screen_GetpLogicGraphic(),&destination,&source,&sChunky);
    Font8x8_PrintColour("GodLib: chunky -> ST 4 planes",Screen_GetpLogic(),8,8,15);
    Font8x8_PrintColour("256x128 / one byte per pixel",Screen_GetpLogic(),8,24,12);
    Font8x8_PrintColour(sPaused?"SPACE: resume   ESC: exit":"SPACE: pause    ESC: exit",
        Screen_GetpLogic(),8,40,15);
    ++gChunkyDemoFrames;
}

S16 GodLib_Game_Main(S16 argc,char **argv)
{
    U16 x,y;
    U8 quit=0;
    U8 *pixels=(U8*)sBackground;
    (void)argc; (void)argv;
    GemDos_Super(0);
    Platform_Init();
    Screen_Init(320,200,eGRAPHIC_COLOURMODE_4PLANE,eSCREEN_SCROLL_NONE);
    Video_SetPalST(sPalette);
    GraphicCanvas_Init(&sChunky,eGRAPHIC_COLOURMODE_8BPP,WIDTH,HEIGHT);
    GraphicCanvas_SetpVRAM(&sChunky,sPixels);
    for(y=0;y<HEIGHT;++y) for(x=0;x<WIDTH;++x)
        pixels[(U32)y*WIDTH+x] = y<20 ? x>>4 : 1+(((x>>4)^(y>>4))&3);
    /* Call ChunkySurface_* directly: no optional 8BPP function table needed. */
    while(!quit) {
        IKBD_Update();
        while(IKBD_GetKbdBytesWaiting()) {
            U8 key=IKBD_PopKbdByte();
            if(key==eIKBDSCAN_ESC) quit=1;
            if(key==eIKBDSCAN_SPACE) sPaused^=1;
        }
        if(quit) break;
        DrawFrame();
        Screen_Update();
    }
    GraphicCanvas_DeInit(&sChunky);
    Screen_DeInit();
    Platform_DeInit();
    return 0;
}
