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
	eSPRITECHUNK_MOUSE,
	eSPRITECHUNK_JOY1,
	eSPRITECHUNK_KEYS
} eSpriteChunkMode;


static S16 SpriteChunk_Clamp( S16 aValue, S16 aMin, S16 aMax )
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


static void SpriteChunk_SetMode( eSpriteChunkMode * apMode, const eSpriteChunkMode aMode, const sGraphicPos * apPos )
{
	if( *apMode == aMode )
	{
		return;
	}

	*apMode = aMode;

	switch( *apMode )
	{
	case eSPRITECHUNK_MOUSE:
		IKBD_EnableMouse();
		IKBD_SetMousePosition( apPos->mX, apPos->mY );
		break;

	case eSPRITECHUNK_KEYS:
	case eSPRITECHUNK_JOY1:
		IKBD_EnableJoysticks();
		break;
	}
}


static void SpriteChunk_ApplyJoy1( sGraphicPos * apPos )
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


/* Each logical page remembers exactly the regions drawn into that page.
 * Store records offsets, not pixels; the clean pixels stay in ScreenBack. */
static sGraphicChunkList sChunkLists[2];
static sGraphicPos sSavedPositions[2];
sGraphicPos gSpriteChunkPos;
volatile U16 gSpriteChunkReady;
volatile U16 gRestoredChunks[2];

static void SpriteChunk_RestoreBackground(U16 index)
{
    gRestoredChunks[index] += sChunkLists[index].mActiveCount;
    Graphic_ChunkList_ReStore(&sChunkLists[index],
        Screen_GetpBackGraphic(),Screen_GetpLogicGraphic());
    /* ReStore clears mActiveCount; the next draw fills this page's list again. */
}

static void SpriteChunk_StoreBackground(U16 index,const sGraphicPos *pos)
{
    sGraphicRect rect;
    rect.mX=pos->mX; rect.mY=pos->mY;
    rect.mWidth=SPRITE_WIDTH; rect.mHeight=SPRITE_HEIGHT;
    /* Store does not clip: clamp the sprite fully inside the canvas first. */
    Graphic_ChunkList_Store(&sChunkLists[index],Screen_GetpLogicGraphic(),&rect);
}

static void SpriteChunk_CopyBackgroundToScreens( const sDegas * apPicture )
{
	Memory_Copy( SCREEN_BYTES, &apPicture->mPixels[ 0 ], Screen_GetpBack() );
	Font8x8_PrintColour( "CHUNK RESTORE / 1: MOUSE", Screen_GetpBack(), 8, 8, 14 );
	Font8x8_PrintColour( "2: JOY1 / 3: ARROW KEYS", Screen_GetpBack(), 8, 18, 14 );
	Font8x8_PrintColour( "SPACE: EXIT (ASM RESTORE)", Screen_GetpBack(), 8, 28, 14 );
	Memory_Copy( SCREEN_BYTES, Screen_GetpBack(), Screen_GetpLogic() );
	Memory_Copy( SCREEN_BYTES, Screen_GetpBack(), Screen_GetpPhysic() );
}


S16 GodLib_Game_Main( S16 aArgCount, char * apArgs[] )
{
	sDegas *		lpBgPicture;
	sDegas *		lpSpritePicture;
	sSprite *		lpSprite;
	U16 *			lpMsk;
	U8				lPosDirty[ 2 ];
	U16				lLogicIndex;
	eSpriteChunkMode	lMode;

	(void)aArgCount;
	(void)apArgs;

	GemDos_Super( 0 );
	Platform_Init();
	File_Init();

	lpBgPicture     = File_Load( "RGLOGO.PI1" );
	lpSpritePicture = File_Load( "SPRITE.PI1" );
	if( !lpBgPicture || !lpSpritePicture )
	{
		printf( "RGLOGO.PI1 or SPRITE.PI1 not found\r\n" );
		GemDos_Cnecin();
		File_UnLoad( lpSpritePicture );
		File_UnLoad( lpBgPicture );
		File_DeInit();
		Platform_DeInit();
		return( 1 );
	}

	Screen_Init( SCREEN_WIDTH, SCREEN_HEIGHT, eGRAPHIC_COLOURMODE_4PLANE, eSCREEN_SCROLL_NONE );
	Video_SetPalST( &lpBgPicture->mHeader.mPalette[ 0 ] );
	Graphic_SetBlitterEnable( BLT_BLITTER );
	SpriteChunk_CopyBackgroundToScreens( lpBgPicture );

	lpMsk    = Sprite_MaskCreate( &lpSpritePicture->mPixels[ 0 ], SPRITE_WIDTH, SPRITE_HEIGHT, 4, 4, 0 );
	lpSprite = Sprite_Create( &lpSpritePicture->mPixels[ 0 ], lpMsk, SPRITE_WIDTH, SPRITE_HEIGHT, 4, 4, 0 );

	gSpriteChunkPos.mX = (SCREEN_WIDTH  - SPRITE_WIDTH ) >> 1;
	gSpriteChunkPos.mY = (SCREEN_HEIGHT - SPRITE_HEIGHT) >> 1;
	lMode   = eSPRITECHUNK_JOY1;
	SpriteChunk_SetMode( &lMode, eSPRITECHUNK_MOUSE, &gSpriteChunkPos );

	sSavedPositions[ 0 ] = gSpriteChunkPos;
	sSavedPositions[ 1 ] = gSpriteChunkPos;
	lPosDirty[ 0 ] = 1;
	lPosDirty[ 1 ] = 1;
    sChunkLists[0].mChunkCount=32;
    sChunkLists[1].mChunkCount=32;
    Graphic_ChunkList_Clear(&sChunkLists[0]);
    Graphic_ChunkList_Clear(&sChunkLists[1]);
    gSpriteChunkReady=1;

	while( !IKBD_GetKeyStatus( eIKBDSCAN_SPACE ) )
	{
		Screen_Update();
		IKBD_Update();
		lLogicIndex = Screen_GetLogicIndex();

		if( IKBD_GetKeyStatus( eIKBDSCAN_1 ) )
		{
			SpriteChunk_SetMode( &lMode, eSPRITECHUNK_MOUSE, &gSpriteChunkPos );
		}
		if( IKBD_GetKeyStatus( eIKBDSCAN_2 ) )
		{
			SpriteChunk_SetMode( &lMode, eSPRITECHUNK_JOY1, &gSpriteChunkPos );
		}

        if(IKBD_GetKeyStatus(eIKBDSCAN_3))
            SpriteChunk_SetMode(&lMode,eSPRITECHUNK_KEYS,&gSpriteChunkPos);

		switch( lMode )
		{
		case eSPRITECHUNK_MOUSE:
			gSpriteChunkPos.mX = IKBD_GetMouseX();
			gSpriteChunkPos.mY = IKBD_GetMouseY();
			break;

        case eSPRITECHUNK_KEYS:
            if(IKBD_GetKeyStatus(eIKBDSCAN_LEFTARROW)) --gSpriteChunkPos.mX;
            if(IKBD_GetKeyStatus(eIKBDSCAN_RIGHTARROW)) ++gSpriteChunkPos.mX;
            if(IKBD_GetKeyStatus(eIKBDSCAN_UPARROW)) --gSpriteChunkPos.mY;
            if(IKBD_GetKeyStatus(eIKBDSCAN_DOWNARROW)) ++gSpriteChunkPos.mY;
            break;
		case eSPRITECHUNK_JOY1:
			SpriteChunk_ApplyJoy1( &gSpriteChunkPos );
			break;
		}

		gSpriteChunkPos.mX = SpriteChunk_Clamp( gSpriteChunkPos.mX, 0, SCREEN_WIDTH  - SPRITE_WIDTH );
		gSpriteChunkPos.mY = SpriteChunk_Clamp( gSpriteChunkPos.mY, 0, SCREEN_HEIGHT - SPRITE_HEIGHT );
		if( lMode == eSPRITECHUNK_MOUSE )
		{
			IKBD_SetMousePosition( gSpriteChunkPos.mX, gSpriteChunkPos.mY );
		}

		if( lPosDirty[ lLogicIndex ] ||
			( gSpriteChunkPos.mX != sSavedPositions[ lLogicIndex ].mX ) ||
			( gSpriteChunkPos.mY != sSavedPositions[ lLogicIndex ].mY ) )
		{
			SpriteChunk_RestoreBackground( lLogicIndex );
			sSavedPositions[ lLogicIndex ] = gSpriteChunkPos;
			Screen_Logic_DrawSprite_Clip( &gSpriteChunkPos, lpSprite );
            SpriteChunk_StoreBackground(lLogicIndex,&gSpriteChunkPos);
			lPosDirty[ lLogicIndex ] = 0;
		}
	}

	Sprite_Destroy( lpSprite );
	Sprite_MaskDestroy( lpMsk );
	File_UnLoad( lpSpritePicture );
	File_UnLoad( lpBgPicture );

	Screen_DeInit();
	File_DeInit();
	Platform_DeInit();

	return( 0 );
}
