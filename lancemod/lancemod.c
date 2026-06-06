/*************************************************************************************
 * GodLib Example Program Suite
 *
 * Demonstrates ProTracker MOD playback through Lance Paula replay.
 ************************************************************************************/


/* ###################################################################################
#  INCLUDES
################################################################################### */

#include <godlib/file/file.h>
#include <godlib/gemdos/gemdos.h>
#include <godlib/ikbd/ikbd.h>
#include <godlib/music/lancemod.h>
#include <godlib/system/system.h>
#include <godlib/vbl/vbl.h>


/* ###################################################################################
#  CODE
################################################################################### */


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
	GemDos_Cconws( "\033E\033f-GodLib LanceMod Sample-\r\n" );
	GemDos_Cconws( "Playing LOSTPARO.MOD at 25 KHz\r\n" );
	GemDos_Cconws( " [F1] - Toggle raster CPU meter\r\n" );
	GemDos_Cconws( " [Space] - Quit\r\n" );
}


static void Test_Loop( void )
{
	void *	lpMod;
	U8		lExitFlag;
	U8		lRasterDebugFlag;

	Menu_Print();

	lpMod = LanceMod_Load( "LOSTPARO.MOD" );
	if( !lpMod )
	{
		GemDos_Cconws( "Could not load LOSTPARO.MOD\r\n" );
		while( !IKBD_GetKbdBytesWaiting() );
		return;
	}

	if( !LanceMod_Start( lpMod, eLANCEMOD_FREQ_25K ) )
	{
		GemDos_Cconws( "Could not install LanceMod VBL callback\r\n" );
		LanceMod_Stop();
		LanceMod_UnLoad( lpMod );
		while( !IKBD_GetKbdBytesWaiting() );
		return;
	}

	lExitFlag = 0;
	lRasterDebugFlag = 0;
	while( !lExitFlag )
	{
		if( IKBD_GetKbdBytesWaiting() )
		{
			U8 lKey;

			lKey = IKBD_PopKbdByte();
			if( eIKBDSCAN_F1 == lKey )
			{
				lRasterDebugFlag ^= 1;
				LanceMod_SetRasterDebug( lRasterDebugFlag );
			}
			else if( eIKBDSCAN_SPACE == lKey )
			{
				lExitFlag = 1;
			}
		}
	}

	LanceMod_StopVbl();
	LanceMod_UnLoad( lpMod );
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
