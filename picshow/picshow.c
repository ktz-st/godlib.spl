/*************************************************************************************
 * GodLib Example Progam Suite
 * 
 * Demonstrates basic screen functionality
 *
 * PINK 01.01.03
 *************************************************************************************
*/

/* ###################################################################################
#  INCLUDES
################################################################################### */

#include	<godlib/gemdos/gemdos.h>
#include	<godlib/graphic/graphic.h>
#include	<godlib/file/file.h>
#include	<godlib/ikbd/ikbd.h>
#include	<godlib/memory/memory.h>
#include	<godlib/pictypes/degas.h>
#include	<godlib/platform/platform.h>
#include	<godlib/screen/screen.h>
#include	<godlib/system/system.h>
#include	<godlib/vbl/vbl.h>
#include	<godlib/video/video.h>



/* ###################################################################################
#  PROTOTYPES
################################################################################### */


void	Test_Loop( void );


/* ###################################################################################
#  DATA
################################################################################### */

sDegas *		gpPicture;


/* ###################################################################################
#  CODE
################################################################################### */

/*-----------------------------------------------------------------------------------*
* FUNCTION : GodLib_Game_Main( S16 aArgCount, char * apArgs[] ) )
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
	gpPicture = File_Load( "RGLOGO.PI1" );

	if( gpPicture )
	{
		Screen_Init( 320, 200, eGRAPHIC_COLOURMODE_4PLANE, eSCREEN_SCROLL_NONE );
		Video_SetPalST( &gpPicture->mHeader.mPalette[ 0 ] );

		while( !IKBD_GetKeyStatus(eIKBDSCAN_SPACE) )
		{
			Screen_Update();
			IKBD_Update();
			Memory_Copy( 32000L, &gpPicture->mPixels[ 0 ], Screen_GetpLogic() );
		}
	}

	File_UnLoad( gpPicture );
}




/* ################################################################################ */
