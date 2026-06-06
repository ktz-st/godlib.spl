/*************************************************************************************
 * GodLib Example Program Suite
 *
 * Demonstrates ProTracker MOD playback through Wizzcat STE replay.
 ************************************************************************************/


/* ###################################################################################
#  INCLUDES
################################################################################### */

#include <godlib/file/file.h>
#include <godlib/gemdos/gemdos.h>
#include <godlib/ikbd/ikbd.h>
#include <godlib/music/wizzcat.h>
#include <godlib/system/system.h>
#include <godlib/vbl/vbl.h>


/* ###################################################################################
#  CODE
################################################################################### */

#define dSAMPLE_SONG_LAST_POS	5


static void Hardware_Init( void )
{
	GemDos_Super( 0 );

	System_Init();
	Vbl_Init();
	IKBD_Init();
	File_Init();
}


static void Hardware_DeInit( void )
{
	File_DeInit();
	IKBD_DeInit();
	Vbl_DeInit();
	System_DeInit();
}


static void Menu_Print( void )
{
	GemDos_Cconws( "\033E\033f-GodLib Wizzcat MOD Sample-\r\n" );
	GemDos_Cconws( "Playing QUICKIE.MOD through STE DMA\r\n" );
	GemDos_Cconws( " [1] - Jump to first song position\r\n" );
	GemDos_Cconws( " [2] - Jump to last song position\r\n" );
	GemDos_Cconws( " [Space] - Quit\r\n\r\n" );
}


static void Status_Print( const char * apString )
{
	GemDos_Cconws( "\033Y* " );
	GemDos_Cconws( "Status: " );
	GemDos_Cconws( apString );
	GemDos_Cconws( "                    " );
}


static void Info_Print( sWizzcatInfo * apInfo )
{
	char			lString[ 64 ];

	lString[ 0 ] = ' ';
	lString[ 1 ] = 'P';
	lString[ 2 ] = 'o';
	lString[ 3 ] = 's';
	lString[ 4 ] = ':';
	lString[ 5 ] = ' ';
	lString[ 6 ] = (char)( '0' + (apInfo->mSongPos / 100) );
	lString[ 7 ] = (char)( '0' + ((apInfo->mSongPos / 10) % 10) );
	lString[ 8 ] = (char)( '0' + (apInfo->mSongPos % 10) );
	lString[ 9 ] = ' ';
	lString[ 10 ] = 'P';
	lString[ 11 ] = 'a';
	lString[ 12 ] = 't';
	lString[ 13 ] = ':';
	lString[ 14 ] = ' ';
	lString[ 15 ] = (char)( '0' + (apInfo->mPattPos / 100) );
	lString[ 16 ] = (char)( '0' + ((apInfo->mPattPos / 10) % 10) );
	lString[ 17 ] = (char)( '0' + (apInfo->mPattPos % 10) );
	lString[ 18 ] = ' ';
	lString[ 19 ] = ' ';
	lString[ 20 ] = '\r';
	lString[ 21 ] = 0;

	GemDos_Cconws( "\033Y( " );
	GemDos_Cconws( lString );
}


static void Test_Loop( void )
{
	sWizzcatModule *	lpMod;
	U8					lExitFlag;
	sWizzcatInfo		lInfo;
	sWizzcatInfo		lLastInfo;

	Menu_Print();

	lpMod = Wizzcat_Load( "QUICKIE.MOD" );
	if( !lpMod )
	{
		GemDos_Cconws( "Could not load QUICKIE.MOD\r\n" );
		while( !IKBD_GetKbdBytesWaiting() );
		return;
	}

	if( !Wizzcat_Start( lpMod ) )
	{
		GemDos_Cconws( "Could not install Wizzcat VBL callback\r\n" );
		Wizzcat_Stop();
		Wizzcat_UnLoad( lpMod );
		while( !IKBD_GetKbdBytesWaiting() );
		return;
	}

	lExitFlag = 0;
	lLastInfo.mSongPos = 0xFF;
	lLastInfo.mPattPos = 0xFF;
	Status_Print( "playing" );
	while( !lExitFlag )
	{
		Wizzcat_GetInfo( &lInfo );
		if( (lInfo.mSongPos != lLastInfo.mSongPos) || (lInfo.mPattPos != lLastInfo.mPattPos) )
		{
			lLastInfo = lInfo;
			Info_Print( &lInfo );
		}

		while( IKBD_GetKbdBytesWaiting() )
		{
			U8 lKey;

			lKey = IKBD_PopKbdByte() & 0x7F;
			if( eIKBDSCAN_1 == lKey )
			{
				Wizzcat_Jump( 1 );
				Status_Print( "jump first" );
			}
			else if( eIKBDSCAN_2 == lKey )
			{
				Wizzcat_Jump( dSAMPLE_SONG_LAST_POS );
				Status_Print( "jump last" );
			}
			else if( eIKBDSCAN_SPACE == lKey )
			{
				lExitFlag = 1;
			}
		}
	}

	Wizzcat_StopVbl();
	Wizzcat_UnLoad( lpMod );
}


S16 GodLib_Game_Main( S16 aArgCount, char * apArgs[] )
{
	(void)aArgCount;
	(void)apArgs;

	Hardware_Init();
	Test_Loop();
	Hardware_DeInit();

	return( 0 );
}


/* ################################################################################ */
