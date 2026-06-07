/*************************************************************************************
 * GodLib Example Program Suite
 *
 * Demonstrates runtime conversion from PI1 font sheets to sFont, then prints with
 * FontPrint, FontPrintLeft, FontPrintRight and FontPrintCentred.
 *************************************************************************************/

#include <stdio.h>

#include <godlib/file/file.h>
#include <godlib/font/font.h>
#include <godlib/gemdos/gemdos.h>
#include <godlib/graphic/graphic.h>
#include <godlib/ikbd/ikbd.h>
#include <godlib/memory/memory.h>
#include <godlib/pictypes/degas.h>
#include <godlib/platform/platform.h>
#include <godlib/screen/screen.h>
#include <godlib/sprite/sprite.h>
#include <godlib/system/system.h>
#include <godlib/vbl/vbl.h>
#include <godlib/video/video.h>


#define SCREEN_WIDTH        320
#define SCREEN_HEIGHT       200
#define FONT_SHEET_COLUMNS   20
#define FONT_CELL_WIDTH      16
#define FONT_CHAR_FIRST       1
#define FONT_CHAR_LAST      127
#define FONT_CHAR_COUNT     (FONT_CHAR_LAST - FONT_CHAR_FIRST + 1)


typedef struct
{
    const char * mpFileName;
    U16          mCellHeight;
    U16          mFixedWidth;
    U8           mSpaceWidth;
    U8           mKerning;
} sFontDef;


static sFont * FontExample_LoadPi1Font( const sFontDef * apDef, U16 * apPalette );
static void    FontExample_DrawPage( sFont * apFont6x6, sFont * apFont8x8, sFont * apFont8x16 );
static void    FontExample_DrawStaticPage( sFont * apFont6x6, sFont * apFont8x8, sFont * apFont8x16 );
static void    FontExample_DrawText( S16 aX, S16 aY, sFont * apFont, const char * apText );
static void    FontExample_DrawTypewriter( sFont * apFont6x6, sFont * apFont8x8, sFont * apFont8x16, const char * apText, S16 aX, S16 aY );
static void    FontExample_WaitSpace( void );


static const sFontDef gFontDefs[] =
{
    { "gfx\\FONT6X6.PI1",  6, 6, 6, 0 },
    { "gfx\\FONT8X8.PI1",  8, 8, 8, 0 },
    { "gfx\\FONT8X16.PI1", 16, 8, 8, 0 }
};


S16 GodLib_Game_Main( S16 aArgCount, char * apArgs[] )
{
    sFont * lpFont6x6;
    sFont * lpFont8x8;
    sFont * lpFont8x16;
    U16     lPalette[ 16 ];

    (void)aArgCount;
    (void)apArgs;

    GemDos_Super( 0 );
    Platform_Init();

    lpFont6x6  = FontExample_LoadPi1Font( &gFontDefs[ 0 ], &lPalette[ 0 ] );
    lpFont8x8  = FontExample_LoadPi1Font( &gFontDefs[ 1 ], 0 );
    lpFont8x16 = FontExample_LoadPi1Font( &gFontDefs[ 2 ], 0 );

    if( !lpFont6x6 || !lpFont8x8 || !lpFont8x16 )
    {
        printf( "Font PI1 files not found in gfx\\\r\n" );
        GemDos_Cnecin();
    }
    else
    {
        Screen_Init( SCREEN_WIDTH, SCREEN_HEIGHT, eGRAPHIC_COLOURMODE_4PLANE, eSCREEN_SCROLL_NONE );
        Video_SetPalST( &lPalette[ 0 ] );
        Graphic_SetBlitterEnable( BLT_BLITTER );

        FontExample_DrawPage( lpFont6x6, lpFont8x8, lpFont8x16 );
        FontExample_WaitSpace();

        Screen_DeInit();
    }

    Font_Destroy( lpFont8x16 );
    Font_Destroy( lpFont8x8 );
    Font_Destroy( lpFont6x6 );

    Platform_DeInit();

    return( 0 );
}


static sFont * FontExample_LoadPi1Font( const sFontDef * apDef, U16 * apPalette )
{
    sDegas *       lpPicture;
    sSpriteBlock * lpBlock;
    sFont *        lpFont;
    U8             lCharMap[ FONT_CHAR_COUNT + 1 ];
    U16 *          lpMask;
    U16            i;
    U16            lChar;
    U16            lX;
    U16            lY;
    U32            lOffset;

    lpPicture = File_Load( apDef->mpFileName );
    if( !lpPicture )
    {
        return( 0 );
    }

    if( apPalette )
    {
        Memory_Copy( sizeof(U16) * 16, &lpPicture->mHeader.mPalette[ 0 ], apPalette );
    }

    lpBlock = Sprite_BlockCreate( FONT_CHAR_COUNT );
    if( !lpBlock )
    {
        File_UnLoad( lpPicture );
        return( 0 );
    }

    for( i=0; i<FONT_CHAR_COUNT; i++ )
    {
        lChar = (U16)(FONT_CHAR_FIRST + i);
        lX    = (U16)((lChar % FONT_SHEET_COLUMNS) * FONT_CELL_WIDTH);
        lY    = (U16)((lChar / FONT_SHEET_COLUMNS) * apDef->mCellHeight);

        lOffset = ((U32)(lX >> 4) << 2);
        lOffset += (U32)lY * 80UL;

        lpMask = Sprite_MaskCreate( &lpPicture->mPixels[ lOffset ], FONT_CELL_WIDTH, apDef->mCellHeight, 4, 4, 0 );
        lpBlock->mpSprite[ i ] = Sprite_Create( &lpPicture->mPixels[ lOffset ], lpMask, FONT_CELL_WIDTH, apDef->mCellHeight, 4, 4, 0 );
        Sprite_MaskDestroy( lpMask );

        lCharMap[ i ] = (U8)lChar;
    }
    lCharMap[ FONT_CHAR_COUNT ] = 0;

    lpFont = Font_Create( lpBlock, &lCharMap[ 0 ], apDef->mFixedWidth );
    if( lpFont )
    {
        lpFont->mSpaceWidth = apDef->mSpaceWidth;
        lpFont->mKerning    = apDef->mKerning;
    }

    Sprite_BlockDestroy( lpBlock );
    File_UnLoad( lpPicture );

    return( lpFont );
}


static void FontExample_DrawPage( sFont * apFont6x6, sFont * apFont8x8, sFont * apFont8x16 )
{
    FontExample_DrawStaticPage( apFont6x6, apFont8x8, apFont8x16 );
    Screen_Update();
    Vbl_WaitVbls( 35 );

    FontExample_DrawTypewriter( apFont6x6, apFont8x8, apFont8x16, "TYPEWRITER EFFECT: ONE LETTER PER FRAME.", 0, 166 );
}


static void FontExample_DrawStaticPage( sFont * apFont6x6, sFont * apFont8x8, sFont * apFont8x16 )
{
    sGraphicRect lRect;

    Screen_Logic_ClearScreen();

    FontExample_DrawText( 8, 8, apFont8x16, "GODLIB FONT EXAMPLE" );
    FontExample_DrawText( 8, 28, apFont6x6, "PI1 sheets loaded and converted at runtime" );

    FontExample_DrawText( 8, 46, apFont8x8, "Screen_Logic_FontPrint" );

    lRect.mX      = 8;
    lRect.mY      = 66;
    lRect.mWidth  = 304;
    lRect.mHeight = 16;
    Graphic_FontPrintLeft( Screen_GetpLogicGraphic(), apFont8x8, &lRect, "Graphic_FontPrintLeft" );

    lRect.mY = 84;
    Graphic_FontPrintRight( Screen_GetpLogicGraphic(), apFont8x8, &lRect, "Graphic_FontPrintRight" );

    lRect.mY = 104;
    Graphic_FontPrintCentred( Screen_GetpLogicGraphic(), apFont8x16, &lRect, "FontPrintCentered" );

    FontExample_DrawText( 8, 132, apFont6x6, "6x6 size" );
    FontExample_DrawText( 92, 130, apFont8x8, "8x8 size" );
    FontExample_DrawText( 184, 124, apFont8x16, "8x16 size" );
}


static void FontExample_DrawText( S16 aX, S16 aY, sFont * apFont, const char * apText )
{
    sGraphicPos lPos;

    lPos.mX = aX;
    lPos.mY = aY;
    Screen_Logic_FontPrint( &lPos, apFont, apText );
}


static void FontExample_DrawTypewriter( sFont * apFont6x6, sFont * apFont8x8, sFont * apFont8x16, const char * apText, S16 aX, S16 aY )
{
    char        lBuffer[ 64 ];
    sGraphicPos lPos;
    U16         i;

    lPos.mX = aX;
    lPos.mY = aY;

    i = 0;
    while( apText[ i ] && (i < (sizeof(lBuffer) - 1)) )
    {
        lBuffer[ i ] = apText[ i ];
        i++;
        lBuffer[ i ] = 0;

        FontExample_DrawStaticPage( apFont6x6, apFont8x8, apFont8x16 );
        Screen_Logic_FontPrint( &lPos, apFont8x8, &lBuffer[ 0 ] );
        Screen_Update();
        Vbl_WaitVbls( 3 );
    }
}


static void FontExample_WaitSpace( void )
{
    while( !IKBD_GetKeyStatus( eIKBDSCAN_SPACE ) )
    {
        IKBD_Update();
        Vbl_WaitVbl();
    }
}
