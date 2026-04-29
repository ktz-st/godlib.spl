/*************************************************************************************
 * GodLib Example Progam Suite
 *
 * Demonstrates IFF ILBM display
 *************************************************************************************
*/

/* ###################################################################################
#  INCLUDES
################################################################################### */

#include	<godlib/file/file.h>
#include	<godlib/gemdos/gemdos.h>
#include	<godlib/ikbd/ikbd.h>
#include	<godlib/memory/memory.h>
#include	<godlib/pictypes/iff.h>
#include	<godlib/platform/platform.h>
#include	<godlib/screen/screen.h>
#include	<godlib/video/video.h>


/* ###################################################################################
#  PROTOTYPES
################################################################################### */

void	Test_Loop( void );


/* ###################################################################################
#  CODE
################################################################################### */

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


void	Test_Loop( void )
{
	void *		lpFile;
	void *		lpPicture;
	sIffIlbm	lIlbm;
	U16			lPalette[ 16 ];
	U16			lWordCount;
	U32			lLineBytes;
	U32			lPictureBytes;

	lpFile = File_Load( "CFTITLE.LBM" );
	if( !lpFile )
	{
		GemDos_Cconws( "Could not load CFTITLE.LBM\r\n" );
		GemDos_Cnecin();
		return;
	}

	if( !Iff_ILBM_Parse( lpFile, &lIlbm ) )
	{
		GemDos_Cconws( "Could not parse CFTITLE.LBM\r\n" );
		GemDos_Cnecin();
		File_UnLoad( lpFile );
		return;
	}

	lWordCount = (U16)((lIlbm.mWidth + 15U) >> 4);
	lLineBytes = (U32)lWordCount << 3;
	lPictureBytes = lLineBytes * lIlbm.mHeight;
	lpPicture = mMEMALLOC( lPictureBytes );
	if( !lpPicture )
	{
		GemDos_Cconws( "Could not allocate picture buffer\r\n" );
		GemDos_Cnecin();
		File_UnLoad( lpFile );
		return;
	}

	if( !Iff_ILBM_DecodeToSTLow( &lIlbm, lpPicture ) )
	{
		GemDos_Cconws( "Could not decode CFTITLE.LBM\r\n" );
		GemDos_Cnecin();
		mMEMFREE( lpPicture );
		File_UnLoad( lpFile );
		return;
	}

	Memory_Clear( sizeof( lPalette ), lPalette );
	Iff_ILBM_CmapToSTE( &lIlbm, lPalette, 16 );

	Screen_Init( 320, 200, eGRAPHIC_COLOURMODE_4PLANE, eSCREEN_SCROLL_NONE );
	Video_SetPalST( &lPalette[ 0 ] );

	while( !IKBD_GetKeyStatus( eIKBDSCAN_SPACE ) )
	{
		U16	y;
		U8 *	lpSrc;
		U8 *	lpDst;

		lpSrc = (U8*)lpPicture;
		lpDst = (U8*)Screen_GetpLogic();
		Screen_Logic_ClearScreen();

		for( y=0; (y<lIlbm.mHeight) && (y<200); y++ )
		{
			Memory_Copy( lLineBytes, lpSrc, lpDst );
			lpSrc += lLineBytes;
			lpDst += 160;
		}

		Screen_Update();
		IKBD_Update();
	}

	mMEMFREE( lpPicture );
	File_UnLoad( lpFile );
}


/* ################################################################################ */
