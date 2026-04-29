/*************************************************************************************
 * GodLib Example Program Suite
 *
 * Demonstrates GraphicCanvas DrawLine, DrawPixel and DrawBox.
 ************************************************************************************/


/* ###################################################################################
#  INCLUDES
################################################################################### */

#include <godlib/font8x8/font8x8.h>
#include <godlib/gemdos/gemdos.h>
#include <godlib/graphic/graphic.h>
#include <godlib/ikbd/ikbd.h>
#include <godlib/platform/platform.h>
#include <godlib/screen/screen.h>
#include <godlib/vbl/vbl.h>
#include <godlib/video/video.h>


/* ###################################################################################
#  DATA
################################################################################### */

static U16	gPalette[ 16 ] =
{
	0x000, 0x777, 0x700, 0x070, 0x007, 0x770, 0x707, 0x077,
	0x333, 0x555, 0x733, 0x373, 0x337, 0x773, 0x737, 0x777
};

static U16				gBlitSourceScreen[ 16000 ];
static sGraphicCanvas	gBlitSourceCanvas;


/* ###################################################################################
#  CODE
################################################################################### */


static void GraphicSample_Draw( U8 aUseBlitter )
{
	sGraphicRect	lRect;
	sGraphicBox		lLine;
	sGraphicPos		lPoint;
	U16				i;

	Screen_Logic_ClearScreen_Clip();

	Font8x8_Print( "GodLib Graphic Sample", Screen_GetpLogic(), 8, 8 );
	Font8x8_Print( "F1: ", Screen_GetpLogic(), 8, 18 );
	if( aUseBlitter )
	{
		Font8x8_Print( "BLITTER FUNCS", Screen_GetpLogic(), 40, 18 );
	}
	else
	{
		Font8x8_Print( "CPU FUNCS    ", Screen_GetpLogic(), 40, 18 );
	}
	Font8x8_Print( "SPACE: EXIT", Screen_GetpLogic(), 8, 28 );

	lRect.mX = 16;
	lRect.mY = 48;
	lRect.mWidth = 64;
	lRect.mHeight = 32;
	Screen_Logic_DrawBox_Clip( &lRect, 4 );

	lRect.mX = 96;
	lRect.mY = 48;
	lRect.mWidth = 48;
	lRect.mHeight = 48;
	Screen_Logic_DrawBox_Clip( &lRect, 12 );

	lRect.mX = 160;
	lRect.mY = 48;
	lRect.mWidth = 96;
	lRect.mHeight = 20;
	Screen_Logic_DrawBox_Clip( &lRect, 5 );

	lPoint.mX = 192;
	lPoint.mY = 76;
	lRect.mX = 24;
	lRect.mY = 24;
	lRect.mWidth = 72;
	lRect.mHeight = 40;
	Screen_Logic_Blit( &lPoint, &lRect, &gBlitSourceCanvas );
	Font8x8_Print( "BLIT", Screen_GetpLogic(), 208, 88 );

	lLine.mX0 = 8;
	lLine.mY0 = 112;
	lLine.mX1 = 304;
	lLine.mY1 = 112;
	Screen_Logic_DrawLine_Clip( &lLine, 15 );

	lLine.mX0 = 8;
	lLine.mY0 = 120;
	lLine.mX1 = 304;
	lLine.mY1 = 184;
	Screen_Logic_DrawLine_Clip( &lLine, 2 );

	lLine.mX0 = 304;
	lLine.mY0 = 120;
	lLine.mX1 = 8;
	lLine.mY1 = 184;
	Screen_Logic_DrawLine_Clip( &lLine, 3 );

	lLine.mX0 = 160;
	lLine.mY0 = 104;
	lLine.mX1 = 160;
	lLine.mY1 = 192;
	Screen_Logic_DrawLine_Clip( &lLine, 6 );

	lLine.mX0 = -32;
	lLine.mY0 = 100;
	lLine.mX1 = 352;
	lLine.mY1 = 176;
	Screen_Logic_DrawLine_Clip( &lLine, 14 );

	for( i=0; i<32; i++ )
	{
		lPoint.mX = 32 + (S16)( i * 7 );
		lPoint.mY = 88 + (S16)( ( i * 13 ) & 31 );
		Screen_Logic_DrawPixel_Clip( &lPoint, (S16)( ( i & 15 ) ) );
	}
}


static void GraphicSample_InitSource( void )
{
	sGraphicRect	lRect;
	sGraphicBox		lLine;

	GraphicCanvas_Init( &gBlitSourceCanvas, eGRAPHIC_COLOURMODE_4PLANE, 320, 200 );
	GraphicCanvas_SetpVRAM( &gBlitSourceCanvas, gBlitSourceScreen );

	gBlitSourceCanvas.mpFuncs->ClearScreen( &gBlitSourceCanvas );

	lRect.mX = 24;
	lRect.mY = 24;
	lRect.mWidth = 72;
	lRect.mHeight = 40;
	gBlitSourceCanvas.mpFuncs->DrawBox( &gBlitSourceCanvas, &lRect, 9 );

	lRect.mX = 32;
	lRect.mY = 32;
	lRect.mWidth = 56;
	lRect.mHeight = 24;
	gBlitSourceCanvas.mpFuncs->DrawBox( &gBlitSourceCanvas, &lRect, 10 );

	lLine.mX0 = 24;
	lLine.mY0 = 24;
	lLine.mX1 = 95;
	lLine.mY1 = 63;
	gBlitSourceCanvas.mpFuncs->DrawLine( &gBlitSourceCanvas, &lLine, 15 );

	lLine.mX0 = 95;
	lLine.mY0 = 24;
	lLine.mX1 = 24;
	lLine.mY1 = 63;
	gBlitSourceCanvas.mpFuncs->DrawLine( &gBlitSourceCanvas, &lLine, 2 );
}


static void Test_Loop( void )
{
	U8	lExitFlag;
	U8	lUseBlitter;

	Screen_Init( 320, 200, eGRAPHIC_COLOURMODE_4PLANE, eSCREEN_SCROLL_NONE );
	Video_SetPalST( &gPalette[ 0 ] );
	GraphicSample_InitSource();

	lExitFlag = 0;
	lUseBlitter = 0;
	Graphic_SetBlitterEnable( lUseBlitter );

	while( !lExitFlag )
	{
		while( IKBD_GetKbdBytesWaiting() )
		{
			U8 lKey;

			lKey = IKBD_PopKbdByte();
			if( eIKBDSCAN_SPACE == lKey )
			{
				lExitFlag = 1;
			}
			else if( eIKBDSCAN_F1 == lKey )
			{
				lUseBlitter ^= 1;
				Graphic_SetBlitterEnable( lUseBlitter );
			}
		}

		GraphicSample_Draw( lUseBlitter );
		Screen_Update();
		Vbl_WaitVbl();
		IKBD_Update();
	}

	Screen_DeInit();
}


S16 GodLib_Game_Main( S16 aArgCount, char * apArgs[] )
{
	(void)aArgCount;
	(void)apArgs;

	GemDos_Super( 0 );

	Platform_Init();
	Test_Loop();
	Platform_DeInit();

	return( 0 );
}


/* ################################################################################ */
