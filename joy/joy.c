/*************************************************************************************
 * GodLib Example Progam Suite
 * 
 * Demonstrates basic joystick functionality
 *
 * PINK 01.01.03
 *************************************************************************************
*/

/* ###################################################################################
#  INCLUDES
################################################################################### */


#include	<godlib/gemdos/gemdos.h>
#include	<godlib/ikbd/ikbd.h>
#include	<godlib/system/system.h>
#include	<godlib/vbl/vbl.h>

#include	<stdio.h>


/* ###################################################################################
#  PROTOTYPES
################################################################################### */

void	Hardware_Init( void );
void	Hardware_DeInit( void );

void	Test_Loop( void );
void	Joystick_PacketDisplay( const U8 aPacket );


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

	Hardware_Init();

	Test_Loop();

	Hardware_DeInit();

	return( 0 );
}


/*-----------------------------------------------------------------------------------*
* FUNCTION : Hardware_Init( void )
* ACTION   : Hardware_Init
* CREATION : 18.12.2002 PNK
*-----------------------------------------------------------------------------------*/

void	Hardware_Init( void )
{
	System_Init();
	Vbl_Init();
	IKBD_Init();
}


/*-----------------------------------------------------------------------------------*
* FUNCTION : Hardware_DeInit( void )
* ACTION   : Hardware_DeInit
* CREATION : 18.12.2002 PNK
*-----------------------------------------------------------------------------------*/

void	Hardware_DeInit( void )
{
	IKBD_DeInit();
	Vbl_DeInit();
	System_DeInit();	
}


/*-----------------------------------------------------------------------------------*
* FUNCTION : Test_Loop( void )
* ACTION   : Test_Loop
* CREATION : 18.12.2002 PNK
*-----------------------------------------------------------------------------------*/

void	Test_Loop( void )
{
	IKBD_EnableJoysticks();

	while( !IKBD_GetKeyStatus(eIKBDSCAN_SPACE) )
	{

		printf(  "JOY0: " );
		Joystick_PacketDisplay( IKBD_GetJoy0Packet() );
		printf( " JOY1: " );
		Joystick_PacketDisplay( IKBD_GetJoy1Packet() );
		printf( "\r\n" );
	}
	
}


/*-----------------------------------------------------------------------------------*
* FUNCTION : Joystick_PacketDisplay( const U8 aPacket )
* ACTION   : Joystick_PacketDisplay
* CREATION : 02.01.2003 PNK
*-----------------------------------------------------------------------------------*/

void	Joystick_PacketDisplay( const U8 aPacket )
{
	if( aPacket & 1 )
	{
		printf( "U %u", aPacket );
	}
	else
	{
		printf( " " );
	}

	if( aPacket & 2 )
	{
		printf( "D %u", aPacket );
	}
	else
	{
		printf( " " );
	}

	if( aPacket & 4 )
	{
		printf( "L %u", aPacket  );
	}
	else
	{
		printf( " " );
	}

	if( aPacket & 8 )
	{
		printf( "R %u", aPacket  );
	}
	else
	{
		printf( " " );
	}

	if( aPacket & 128 )
	{
		printf( " FIRE" );
	}
	else
	{
		printf( "     " );
	}
}



/* ################################################################################ */
