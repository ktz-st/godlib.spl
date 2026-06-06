#include	<stdio.h>

#include	<godlib/file/file.h>
#include	<godlib/font8x8/font8x8.h>
#include	<godlib/gemdos/gemdos.h>
#include	<godlib/graphic/graphic.h>
#include	<godlib/ikbd/ikbd.h>
#include	<godlib/memory/memory.h>
#include	<godlib/platform/platform.h>
#include	<godlib/pictypes/degas.h>
#include	<godlib/screen/screen.h>
#include	<godlib/sprite/sprite.h>
#include	<godlib/system/system.h>
#include	<godlib/video/video.h>


#define	SPRITE_WIDTH	16
#define	SPRITE_HEIGHT	16
#define	SCREEN_WIDTH	320
#define	SCREEN_HEIGHT	200
#define	SCREEN_BYTES	32000L
#define	JOY_SPEED		2


typedef enum
{
	eSPRITEBG_MOUSE,
	eSPRITEBG_JOY1
} eSpriteBgMode;


static S16 SpriteBg_Clamp( S16 aValue, S16 aMin, S16 aMax )
{
	if( aValue < aMin )
	{
		return( aMin );
	}
	if( aValue > aMax )
	{
		return( aMax );
	}
	return( aValue );
}


static void SpriteBg_SetMode( eSpriteBgMode * apMode, const eSpriteBgMode aMode, const sGraphicPos * apPos )
{
	if( *apMode == aMode )
	{
		return;
	}

	*apMode = aMode;

	switch( *apMode )
	{
	case eSPRITEBG_MOUSE:
		IKBD_EnableMouse();
		IKBD_SetMousePosition( apPos->mX, apPos->mY );
		break;

	case eSPRITEBG_JOY1:
		IKBD_EnableJoysticks();
		break;
	}
}


static void SpriteBg_ApplyJoy1( sGraphicPos * apPos )
{
	const U8	lJoy = IKBD_GetJoy1Packet();

	if( lJoy & 1 )
	{
		apPos->mY -= JOY_SPEED;
	}
	if( lJoy & 2 )
	{
		apPos->mY += JOY_SPEED;
	}
	if( lJoy & 4 )
	{
		apPos->mX -= JOY_SPEED;
	}
	if( lJoy & 8 )
	{
		apPos->mX += JOY_SPEED;
	}
	if( lJoy & 128 )
	{
		apPos->mX = (SCREEN_WIDTH  - SPRITE_WIDTH ) >> 1;
		apPos->mY = (SCREEN_HEIGHT - SPRITE_HEIGHT) >> 1;
	}
}


static void SpriteBg_RestoreBackground( const sGraphicPos * apPos )
{
	sGraphicRect	lRect;

	lRect.mX      = apPos->mX;
	lRect.mY      = apPos->mY;
	lRect.mWidth  = SPRITE_WIDTH;
	lRect.mHeight = SPRITE_HEIGHT;

	Screen_Logic_Blit_Clip( (sGraphicPos *)apPos, &lRect, Screen_GetpBackGraphic() );
}


static void SpriteBg_CopyBackgroundToScreens( const sDegas * apPicture )
{
	Memory_Copy( SCREEN_BYTES, &apPicture->mPixels[ 0 ], Screen_GetpBack() );
	Font8x8_PrintColour( "1: MOUSE", Screen_GetpBack(), 8, 8, 14 );
	Font8x8_PrintColour( "2: JOY1", Screen_GetpBack(), 8, 18, 14 );
	Font8x8_PrintColour( "SPACE: EXIT", Screen_GetpBack(), 8, 28, 14 );
	Memory_Copy( SCREEN_BYTES, Screen_GetpBack(), Screen_GetpLogic() );
	Memory_Copy( SCREEN_BYTES, Screen_GetpBack(), Screen_GetpPhysic() );
}


S16 GodLib_Game_Main( S16 aArgCount, char * apArgs[] )
{
	sDegas *		lpBgPicture;
	sDegas *		lpSpritePicture;
	sSprite *		lpSprite;
	U16 *			lpMsk;
	sGraphicPos		lPos;
	sGraphicPos		lPosSaved[ 2 ];
	U8				lPosDirty[ 2 ];
	U16				lLogicIndex;
	eSpriteBgMode	lMode;

	(void)aArgCount;
	(void)apArgs;

	GemDos_Super( 0 );
	Platform_Init();

	lpBgPicture     = File_Load( "RGLOGO.PI1" );
	lpSpritePicture = File_Load( "SPRITE.PI1" );
	if( !lpBgPicture || !lpSpritePicture )
	{
		printf( "RGLOGO.PI1 or SPRITE.PI1 not found\r\n" );
		GemDos_Cnecin();
		File_UnLoad( lpSpritePicture );
		File_UnLoad( lpBgPicture );
		Platform_DeInit();
		return( 1 );
	}

	Screen_Init( SCREEN_WIDTH, SCREEN_HEIGHT, eGRAPHIC_COLOURMODE_4PLANE, eSCREEN_SCROLL_NONE );
	Video_SetPalST( &lpBgPicture->mHeader.mPalette[ 0 ] );
	Graphic_SetBlitterEnable( BLT_BLITTER );
	SpriteBg_CopyBackgroundToScreens( lpBgPicture );

	lpMsk    = Sprite_MaskCreate( &lpSpritePicture->mPixels[ 0 ], SPRITE_WIDTH, SPRITE_HEIGHT, 4, 4, 0 );
	lpSprite = Sprite_Create( &lpSpritePicture->mPixels[ 0 ], lpMsk, SPRITE_WIDTH, SPRITE_HEIGHT, 4, 4, 0 );

	lPos.mX = (SCREEN_WIDTH  - SPRITE_WIDTH ) >> 1;
	lPos.mY = (SCREEN_HEIGHT - SPRITE_HEIGHT) >> 1;
	lMode   = eSPRITEBG_JOY1;
	SpriteBg_SetMode( &lMode, eSPRITEBG_MOUSE, &lPos );

	lPosSaved[ 0 ] = lPos;
	lPosSaved[ 1 ] = lPos;
	lPosDirty[ 0 ] = 1;
	lPosDirty[ 1 ] = 1;

	while( !IKBD_GetKeyStatus( eIKBDSCAN_SPACE ) )
	{
		Screen_Update();
		IKBD_Update();
		lLogicIndex = Screen_GetLogicIndex();

		if( IKBD_GetKeyStatus( eIKBDSCAN_1 ) )
		{
			SpriteBg_SetMode( &lMode, eSPRITEBG_MOUSE, &lPos );
		}
		if( IKBD_GetKeyStatus( eIKBDSCAN_2 ) )
		{
			SpriteBg_SetMode( &lMode, eSPRITEBG_JOY1, &lPos );
		}

		switch( lMode )
		{
		case eSPRITEBG_MOUSE:
			lPos.mX = IKBD_GetMouseX();
			lPos.mY = IKBD_GetMouseY();
			break;

		case eSPRITEBG_JOY1:
			SpriteBg_ApplyJoy1( &lPos );
			break;
		}

		lPos.mX = SpriteBg_Clamp( lPos.mX, 0, SCREEN_WIDTH  - SPRITE_WIDTH );
		lPos.mY = SpriteBg_Clamp( lPos.mY, 0, SCREEN_HEIGHT - SPRITE_HEIGHT );
		if( lMode == eSPRITEBG_MOUSE )
		{
			IKBD_SetMousePosition( lPos.mX, lPos.mY );
		}

		if( lPosDirty[ lLogicIndex ] ||
			( lPos.mX != lPosSaved[ lLogicIndex ].mX ) ||
			( lPos.mY != lPosSaved[ lLogicIndex ].mY ) )
		{
			SpriteBg_RestoreBackground( &lPosSaved[ lLogicIndex ] );
			lPosSaved[ lLogicIndex ] = lPos;
			Screen_Logic_DrawSprite_Clip( &lPos, lpSprite );
			lPosDirty[ lLogicIndex ] = 0;
		}
	}

	Sprite_Destroy( lpSprite );
	Sprite_MaskDestroy( lpMsk );
	File_UnLoad( lpSpritePicture );
	File_UnLoad( lpBgPicture );

	Platform_DeInit();

	return( 0 );
}
