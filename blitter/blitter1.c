/*************************************************************************************
 * GodLib Example Progam Suite
 * 
 * Demonstrates basic blitter functionality
 *
 *  Note: Blitter has to be enabled in GEM [OPTIONS->BLITTER] for this to work
 *  F1 toggles between direct Blitter_* calls and the old CPU drawing path
 * 
 * PINK 05.01.18
 *************************************************************************************
*/

/* ###################################################################################
#  INCLUDES
################################################################################### */

#include	<godlib/gemdos/gemdos.h>
#include	<godlib/file/file.h>
#include	<godlib/font8x8/font8x8.h>
#include	<godlib/ikbd/ikbd.h>
#include	<godlib/platform/platform.h>
#include	<godlib/pictypes/degas.h>
#include	<godlib/screen/screen.h>
#include	<godlib/sprite/sprite.h>
#include	<godlib/vbl/vbl.h>
#include	<godlib/video/video.h>
#include	<godlib/blitter/blitter.h>


/* ###################################################################################
#  PROTOTYPES
################################################################################### */

void	Test_Loop( void );
void	Test_DrawCopyBoxPattern( U16 * apScreen, U8 aUseBlitter );
void	Test_DrawBox( U16 * apScreen, U16 aX, U16 aY, U16 aWidth, U16 aHeight, U16 aColour, U8 aUseBlitter );


/* ###################################################################################
#  DATA
################################################################################### */

sDegas *		gpPicture;


/*-----------------------------------------------------------------------------------*
* FUNCTION : Test_DrawBox( U16 * apScreen, U16 aX, U16 aY, U16 aWidth, U16 aHeight, U16 aColour, U8 aUseBlitter )
* ACTION   : draws a small low-res box using either the blitter API or the old CPU path
* CREATION : 29.04.2026
*-----------------------------------------------------------------------------------*/

void	Test_DrawBox( U16 * apScreen, U16 aX, U16 aY, U16 aWidth, U16 aHeight, U16 aColour, U8 aUseBlitter )
{
	sGraphicRect	lRect;
	sBlitterBox		lBox;

	if( aUseBlitter )
	{
		lBox.Width  = aWidth;
		lBox.Height = aHeight;
		lBox.Colour = aColour;
		Blitter_DrawBox( &lBox, apScreen, aX, aY );
	}
	else
	{
		lRect.mX      = aX;
		lRect.mY      = aY;
		lRect.mWidth  = aWidth;
		lRect.mHeight = aHeight;
		Screen_Logic_DrawBox_Clip( &lRect, aColour );
	}
}


/*-----------------------------------------------------------------------------------*
* FUNCTION : Test_DrawCopyBoxPattern( U16 * apScreen, U8 aUseBlitter )
* ACTION   : exercises Blitter_CopyBox with a non word-aligned destination
* CREATION : 29.04.2026
*-----------------------------------------------------------------------------------*/

void	Test_DrawCopyBoxPattern( U16 * apScreen, U8 aUseBlitter )
{
	Test_DrawBox( apScreen, 216,  32, 72, 96, 0, aUseBlitter );
	Test_DrawBox( apScreen, 224,  40, 48,  8, 2, aUseBlitter );
	Test_DrawBox( apScreen, 224,  48, 48,  8, 3, aUseBlitter );
	Test_DrawBox( apScreen, 224,  56, 48,  8, 4, aUseBlitter );
	Test_DrawBox( apScreen, 224,  64, 48,  8, 5, aUseBlitter );

	if( aUseBlitter )
	{
		Blitter_CopyBox( apScreen, apScreen, 224, 40, 231, 88, 48, 32 );
	}
	else
	{
		sGraphicRect	lRect;

		lRect.mX      = 231;
		lRect.mY      = 88;
		lRect.mWidth  = 48;
		lRect.mHeight = 32;
		Screen_Logic_DrawBox_Clip( &lRect, 1 );
		Font8x8_Print( "CPU", apScreen, 240, 100 );
	}
}


/* ###################################################################################
#  CODE
################################################################################### */

/*-----------------------------------------------------------------------------------*
* FUNCTION : main( void )
* ACTION   : it begins  ...
* CREATION : 02.01.2015 PNK
*-----------------------------------------------------------------------------------*/

S16	GodLib_Game_Main( S16 aArgCount, char * apArgs[] )
{
	(void)aArgCount;
	(void)apArgs;
	
	GemDos_Super( 0 );

	Platform_Init();

	Test_Loop();

	Platform_DeInit();

	return( 0 );
}


/*-----------------------------------------------------------------------------------*
* FUNCTION : Test_Loop( void )
* ACTION   : Test_Loop
* CREATION : 18.12.2002 PNK
*-----------------------------------------------------------------------------------*/

void	Test_Loop( void )
{
	sGraphicPos		lPosSaved[ 2 ];
	sGraphicPos		lPos;
	sGraphicRect	lRect;
	S16				lAddX,lAddY;
	sSprite *		lpSprite;
	U16 *			lpMsk;
	U8				exitFlag = 0;
	U8				lUseBlitter = 1;

	/* turn the blitter on */
	/* NOTE: blitter must be enabled in GEM (OPTIONS->BLITTER on desktop) */
	Graphic_SetBlitterEnable( 1 );

	gpPicture = File_Load( "SPRITE.PI1" );

	if( !gpPicture )
	{
		printf( "couldn't find sprite file" );
		GemDos_Cnecin();
		return;
	}

	Screen_Init( 320, 200, eGRAPHIC_COLOURMODE_4PLANE, eSCREEN_SCROLL_NONE );

	Video_SetPalST( &gpPicture->mHeader.mPalette[ 0 ] );

	lPos.mX = 0;
	lPos.mY = 24;

	lPosSaved[ 0 ] = lPos;
	lPosSaved[ 1 ] = lPos;

	/* generate a mask for the sprite	*/
	/* when using tools pipeline, this is generally done with the MASKMAKE tool, and the sprite is constructed with BSBMAKER */

	lpMsk = Sprite_MaskCreate(
		&gpPicture->mPixels[ 0 ],	/* source graphics */
		16,	/* width */
		16,	/* height */
		4,	/* planes */
		4,	/* mask planes */
		0	/* opaque flag */
		);

	lpSprite = Sprite_Create(
		&gpPicture->mPixels[ 0 ],	/* source graphics */
		lpMsk,	/* source mask */
		16,	/* width */
		16,	/* height */
		4,	/* planes */
		4,	/* mask planes */
		0	/* opaque flag */
		);

	Sprite_MaskDestroy( lpMsk );

	lAddX = 1;
	lAddY = 1;

	while( !exitFlag )
	{
		U16 onOffX = 15 * 8;

		while( IKBD_GetKbdBytesWaiting() )
		{
			U8 key = IKBD_PopKbdByte();
			if( eIKBDSCAN_SPACE == key )
			{
				exitFlag = 1;
			}
			else if( eIKBDSCAN_F1 == key )
			{
				/* toggle the sample between CPU drawing and direct Blitter_* calls */
				lUseBlitter ^= 1;
				Graphic_SetBlitterEnable( lUseBlitter );
			}
		}

		Screen_Update();
		IKBD_Update();

		Font8x8_Print( "F1: BLITTER API [ O", Screen_GetpLogic(), 0, 0 );
		if( lUseBlitter )
		{
			Font8x8_Print( "N ] ", Screen_GetpLogic(), onOffX + 4 * 8, 0 );
		}
		else
		{
			Font8x8_Print( "FF ]", Screen_GetpLogic(), onOffX + 4 * 8, 0 );
		}
		Font8x8_Print( "SPACE: EXIT", Screen_GetpLogic(), 0, 8 );

		Test_DrawCopyBoxPattern( Screen_GetpLogic(), lUseBlitter );
		if( lUseBlitter )
		{
			Blitter_DrawOpaqueSprite( (sBlitterSprite *)lpSprite, Screen_GetpLogic(), 196, 136 );
			Blitter_DrawColouredSprite( (sBlitterSprite *)lpSprite, Screen_GetpLogic(), 196, 160, 12 );
		}

		/* clear old sprite */
		lRect.mX = lPosSaved[ Screen_GetLogicIndex() ].mX;
		lRect.mY = lPosSaved[ Screen_GetLogicIndex() ].mY;
		lRect.mWidth = 16;
		lRect.mHeight = 16;
		if( lUseBlitter )
		{
			Test_DrawBox( Screen_GetpLogic(), lRect.mX, lRect.mY, lRect.mWidth, lRect.mHeight, 0, 1 );
		}
		else
		{
			Screen_Logic_DrawBox_Clip( &lRect, 0 );
		}

		/* save current sprite position*/
		lPosSaved[ Screen_GetLogicIndex() ] = lPos;

		/* draw new sprite to logical screen (backbuffer) */
		if( lUseBlitter )
		{
			Blitter_DrawSprite( (sBlitterSprite *)lpSprite , Screen_GetpLogic(), lPos.mX, lPos.mY );
		}
		else
		{
			Screen_Logic_DrawSprite_Clip( &lPos, lpSprite );
		}
		/* calculate new sprite pos */
		lPos.mX += lAddX;

		if( lPos.mX >= (188-16) )
			lAddX  = -1;
		else if( lPos.mX < 0 )
			lAddX  = 1;

		lPos.mY += lAddY;

		if( lPos.mY >= (200-16) )
			lAddY  = -1;
		else if( lPos.mY < 24 )
			lAddY  = 1;
	}

	File_UnLoad( gpPicture );
}


/* ################################################################################ */
