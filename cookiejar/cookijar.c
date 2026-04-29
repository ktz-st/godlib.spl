/*************************************************************************************
 * GodLib Example Progam Suite
 * 
 * Demonstrates cookiejar functionality
 *
 * PINK 01.01.03
 *************************************************************************************
*/

/* ###################################################################################
#  INCLUDES
################################################################################### */

#include	<godlib/cookie/cookie.h>
#include	<godlib/gemdos/gemdos.h>

#include	<stdio.h>


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
	const U32 lMchCookie = mSTRING_TO_U32( '_', 'M', 'C', 'H' );

	(void)aArgCount;
	(void)apArgs;
	
	GemDos_Super( 0 );

	if( CookieJar_Exists() )
	{
		if( CookieJar_CookieExists( lMchCookie ) )
		{
			printf( "_MCH value : %lX\r\n", CookieJar_GetCookieValue( lMchCookie ) );
		}
		else
		{
			printf( "_MCH Cookie not found\r\n" );
		}
	}
	else
	{
		printf( "No Cookie Jar found\r\n" );
	}

	GemDos_Cnecin();

	return( 0 );
}


/* ################################################################################ */
