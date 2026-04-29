/*************************************************************************************
 * GodLib Example Program Suite
 *
 * Demonstrates display of an uncompressed Amiga RAW picture.
 ************************************************************************************/

/* ################################################################################### */

#include	<godlib/file/file.h>
#include	<godlib/gemdos/gemdos.h>
#include	<godlib/ikbd/ikbd.h>
#include	<godlib/memory/memory.h>
#include	<godlib/pictypes/amigaraw.h>
#include	<godlib/platform/platform.h>
#include	<godlib/screen/screen.h>
#include	<godlib/video/video.h>

/* ################################################################################### */

static void	Test_Loop( void );

/* ################################################################################### */

S16	GodLib_Game_Main( S16 aArgCount, char * apArgs[] )
{
	(void)aArgCount;
	(void)apArgs;

	GemDos_Super( 0 );

	Platform_Init();
	File_Init();

	Test_Loop();

	File_DeInit();
	Platform_DeInit();

	return( 0 );
}


static void	Test_Loop( void )
{
	sAmigaRaw *	lpRaw;
	U16 *		lpPicture;
	U16			lPalette[ dAMIGARAW_COLOURS ];

	lpRaw = (sAmigaRaw*)File_Load( "1.RAW" );
	if( !lpRaw )
	{
		GemDos_Cconws( "Could not load 1.RAW\r\n" );
		GemDos_Cnecin();
		return;
	}

	lpPicture = (U16*)mMEMALLOC( dAMIGARAW_HEIGHT * 160UL );
	if( !lpPicture )
	{
		GemDos_Cconws( "Could not allocate picture buffer\r\n" );
		GemDos_Cnecin();
		File_UnLoad( lpRaw );
		return;
	}

	AmigaRaw_PaletteToST( &lpRaw->mPalette[ 0 ], &lPalette[ 0 ], dAMIGARAW_COLOURS );
	AmigaRaw_To4Plane( lpRaw, lpPicture );

	Screen_Init( dAMIGARAW_WIDTH, dAMIGARAW_HEIGHT, eGRAPHIC_COLOURMODE_4PLANE, eSCREEN_SCROLL_NONE );
	Video_SetPalST( &lPalette[ 0 ] );

	while( !IKBD_GetKeyStatus( eIKBDSCAN_SPACE ) )
	{
		Memory_Copy( dAMIGARAW_HEIGHT * 160UL, lpPicture, Screen_GetpLogic() );
		Screen_Update();
		IKBD_Update();
	}

	mMEMFREE( lpPicture );
	File_UnLoad( lpRaw );
}

/* ################################################################################### */
