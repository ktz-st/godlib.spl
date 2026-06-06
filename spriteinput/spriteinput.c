#include	<stdio.h>

#include	<godlib/file/file.h>
#include	<godlib/gemdos/gemdos.h>
#include	<godlib/graphic/graphic.h>
#include	<godlib/ikbd/ikbd.h>
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
#define	JOY_SPEED		2


typedef enum
{
	eSPRITEINPUT_MOUSE,
	eSPRITEINPUT_JOY1
} eSpriteInputMode;


static S16 SpriteInput_Clamp( S16 aValue, S16 aMin, S16 aMax )
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


static void SpriteInput_SetMode( eSpriteInputMode * apMode, const eSpriteInputMode aMode, const sGraphicPos * apPos )
{
	if( *apMode == aMode )
	{
		return;
	}

	*apMode = aMode;

	switch( *apMode )
	{
	case eSPRITEINPUT_MOUSE:
		IKBD_EnableMouse();
		IKBD_SetMousePosition( apPos->mX, apPos->mY );
		break;

	case eSPRITEINPUT_JOY1:
		IKBD_EnableJoysticks();
		break;
	}
}


static void SpriteInput_ApplyJoy1( sGraphicPos * apPos )
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
		IKBD_SetMousePosition( apPos->mX, apPos->mY );
	}
}


S16 GodLib_Game_Main( S16 aArgCount, char * apArgs[] )
{
	sDegas *		gpPicture;
	sSprite *		lpSprite;
	U16 *			lpMsk;
	sGraphicRect	lOldRect;
	sGraphicPos		lPos;
	sGraphicPos		lPosSaved[ 2 ];
	U16				lLogicIndex;
	eSpriteInputMode	lMode;

	(void)aArgCount;
	(void)apArgs;

	GemDos_Super( 0 );
	Platform_Init();

	gpPicture = File_Load( "SPRITE.PI1" );
	if( !gpPicture )
	{
		printf( "SPRITE.PI1 not found\r\n" );
		GemDos_Cnecin();
		Platform_DeInit();
		return( 1 );
	}

	Screen_Init( SCREEN_WIDTH, SCREEN_HEIGHT, eGRAPHIC_COLOURMODE_4PLANE, eSCREEN_SCROLL_NONE );
	Video_SetPalST( &gpPicture->mHeader.mPalette[ 0 ] );
	Graphic_SetBlitterEnable( BLT_BLITTER );

	lpMsk    = Sprite_MaskCreate( &gpPicture->mPixels[ 0 ], SPRITE_WIDTH, SPRITE_HEIGHT, 4, 4, 0 );
	lpSprite = Sprite_Create( &gpPicture->mPixels[ 0 ], lpMsk, SPRITE_WIDTH, SPRITE_HEIGHT, 4, 4, 0 );

	lPos.mX = (SCREEN_WIDTH  - SPRITE_WIDTH ) >> 1;
	lPos.mY = (SCREEN_HEIGHT - SPRITE_HEIGHT) >> 1;
	lMode   = eSPRITEINPUT_JOY1;
	SpriteInput_SetMode( &lMode, eSPRITEINPUT_MOUSE, &lPos );
	IKBD_SetMousePosition( lPos.mX, lPos.mY );

	lPosSaved[ 0 ] = lPos;
	lPosSaved[ 1 ] = lPos;

	while( !IKBD_GetKeyStatus( eIKBDSCAN_SPACE ) )
	{
		Screen_Update();
		IKBD_Update();

		if( IKBD_GetKeyStatus( eIKBDSCAN_1 ) )
		{
			SpriteInput_SetMode( &lMode, eSPRITEINPUT_MOUSE, &lPos );
		}
		if( IKBD_GetKeyStatus( eIKBDSCAN_2 ) )
		{
			SpriteInput_SetMode( &lMode, eSPRITEINPUT_JOY1, &lPos );
		}

		lLogicIndex = Screen_GetLogicIndex();
		lOldRect.mX      = lPosSaved[ lLogicIndex ].mX;
		lOldRect.mY      = lPosSaved[ lLogicIndex ].mY;
		lOldRect.mWidth  = SPRITE_WIDTH;
		lOldRect.mHeight = SPRITE_HEIGHT;
		Screen_Logic_DrawBox_Clip( &lOldRect, 0 );

		switch( lMode )
		{
		case eSPRITEINPUT_MOUSE:
			lPos.mX = IKBD_GetMouseX();
			lPos.mY = IKBD_GetMouseY();
			break;

		case eSPRITEINPUT_JOY1:
			SpriteInput_ApplyJoy1( &lPos );
			break;
		}

		lPos.mX = SpriteInput_Clamp( lPos.mX, 0, SCREEN_WIDTH  - SPRITE_WIDTH );
		lPos.mY = SpriteInput_Clamp( lPos.mY, 0, SCREEN_HEIGHT - SPRITE_HEIGHT );
		if( lMode == eSPRITEINPUT_MOUSE )
		{
			IKBD_SetMousePosition( lPos.mX, lPos.mY );
		}

		lPosSaved[ lLogicIndex ] = lPos;
		Screen_Logic_DrawSprite_Clip( &lPos, lpSprite );
	}

	Sprite_Destroy( lpSprite );
	Sprite_MaskDestroy( lpMsk );
	File_UnLoad( gpPicture );

	Platform_DeInit();

	return( 0 );
}
