#include <godlib/gemdos/gemdos.h>
#include <godlib/graphic/graphic.h>
#include <godlib/font8x8/font8x8.h>
#include <godlib/ikbd/ikbd.h>
#include <godlib/platform/platform.h>
#include <godlib/screen/screen.h>
#include <godlib/vbl/vbl.h>
#include <godlib/video/video.h>
extern void Scroll_Shift(void),Scroll_Insert(void),Scroll_Draw(void);
extern U8 Scroll_Font[];
U16 gScrollBuffer[27*22],gScrollShift;
U8 *gScrollGlyph,*gScrollScreen;
volatile U16 gScrollReady,gScrollExited,gScrollPaused,gScrollSpeed=4;
volatile U32 gScrollFrames;
volatile U32 gScrollLastVbl,gScrollMissedVbl;
static const char gText[]="SIEMKA!  GODLIB PRESENTS A FAST AND SIMPLE BUGSY SCROLLER.    "
    "NO WAVES... JUST BIG LETTERS MOVING ACROSS YOUR ATARI ST!    "
    "ONE SHIFT PASS, ONE SMALL STRIP TO DRAW.    "
    "GREETINGS TO ALL ST AND STE CODERS!    ";
U16 gScrollTextPos,gScrollGlyphPixel;
static void Insert(void)
{
    U16 ch=(U8)gText[gScrollTextPos++];
    if(!gText[gScrollTextPos])gScrollTextPos=0;
    gScrollGlyph=Scroll_Font+(U32)(ch-32)*108;Scroll_Insert();
}
static void Shift(U16 pixels)
{
    gScrollShift=pixels;Scroll_Shift();
}
static void Advance(void)
{
    U16 first=gScrollSpeed,left=32-gScrollGlyphPixel;
    if(first>=left) {
        Shift(left);Insert();gScrollGlyphPixel=0;first-=left;
    }
    if(first){Shift(first);gScrollGlyphPixel+=first;}
}
static void Prepare(void)
{
    static U16 pal[16]={0x001,0x773,0x123,0x234,0x345,0x456,0x567,0x777,
                                  0x100,0x200,0x300,0x400,0x500,0x600,0x700,0x777};
    sGraphicCanvas *c=Screen_GetpBackGraphic();sGraphicRect r;U16 i,j;
    GraphicCanvas_ClearScreen(c);
    Font8x8_PrintColourCanvas("G O D L I B",c,120,24,7);
    Font8x8_PrintColourCanvas("FAST BUGSY SCROLLER",c,88,48,6);
    Font8x8_PrintColourCanvas("SPACE PAUSE   1/2/3/4 SPEED",c,56,152,6);
    Font8x8_PrintColourCanvas("ESC EXIT",c,128,176,7);
    r.mX=0;r.mY=78;r.mWidth=320;r.mHeight=1;GraphicCanvas_DrawBox(c,&r,4);
    r.mY=120;GraphicCanvas_DrawBox(c,&r,4);
    GraphicCanvas_CopyScreen(Screen_GetpLogicGraphic(),Screen_GetpBack());
    GraphicCanvas_CopyScreen(Screen_GetpPhysicGraphic(),Screen_GetpBack());
    Video_SetPalST(pal);
    /* Fill the conveyor at startup so the first screen already has text. */
    Insert();
    for(i=0;i<10;++i){for(j=0;j<4;++j)Shift(8);Insert();}
}
S16 GodLib_Game_Main(S16 argc,char **argv)
{
    U16 quit=0;
    (void)argc;(void)argv;GemDos_Super(0);Platform_Init();
    Screen_Init(320,200,eGRAPHIC_COLOURMODE_4PLANE,0);
    if(!gScreenClass.mpMemBase){Platform_DeInit();return 1;}
    Prepare();
    gScrollScreen=(U8*)Screen_GetpLogic();Scroll_Draw();
    gScrollScreen=(U8*)Screen_GetpPhysic();Scroll_Draw();gScrollReady=1;
    while(!quit) {
        U32 now;
        Screen_Update();now=Vbl_GetCounter();
        if(gScrollFrames && now-gScrollLastVbl>1)gScrollMissedVbl+=now-gScrollLastVbl-1;
        gScrollLastVbl=now;IKBD_Update();
        while(IKBD_GetKbdBytesWaiting()) {
            U8 k=IKBD_PopKbdByte();
            if(k==eIKBDSCAN_ESC)quit=1;
            if(k==eIKBDSCAN_SPACE)gScrollPaused^=1;
            if(k>=eIKBDSCAN_1 && k<=eIKBDSCAN_4)gScrollSpeed=1<<(k-eIKBDSCAN_1);
        }
        if(!gScrollPaused)Advance();
        gScrollScreen=(U8*)Screen_GetpLogic();Scroll_Draw();++gScrollFrames;
    }
    Screen_DeInit();Platform_DeInit();gScrollExited=1;return 0;
}
