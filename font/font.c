/*************************************************************************************
 * GodLib Example Progam Suite
 *
 * Demonstrates 8x8 font printing, including coloured text (Font8x8_PrintColour)
 *
 * PINK 15.05.26
 *************************************************************************************
*/

/* ###################################################################################
#  INCLUDES
################################################################################### */

#include	<godlib/gemdos/gemdos.h>
#include	<godlib/font8x8/font8x8.h>
#include	<godlib/graphic/graphic.h>
#include	<godlib/ikbd/ikbd.h>
#include	<godlib/memory/memory.h>
#include	<godlib/system/system.h>
#include	<godlib/vbl/vbl.h>
#include	<godlib/video/video.h>


/* ###################################################################################
#  PROTOTYPES
################################################################################### */

void	Hardware_Init( void );
void	Hardware_DeInit( void );

void	Test_Loop( void );
void	Font_DrawDemo( U16 * apScreen );

/* ###################################################################################
#	DATA
################################################################################### */

/* index 0 = black background, 1..15 = distinct colours (STe 0x0RGB) */
U16				gMyPalette[ 16 ] =
{
	0x000,0xFFF,0xF00,0x0F0,0x00F,0xFF0,0x0FF,0xF0F,
	0x888,0xF80,0x8F0,0x08F,0xF08,0x80F,0x0F8,0x444
};

/* ###################################################################################
#  CODE
################################################################################### */

/*-----------------------------------------------------------------------------------*
* FUNCTION : GodLib_Game_Main( S16 aArgCount, char * apArgs[] ) )
* ACTION   : it begins  ...
* CREATION : 15.05.26 PNK
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
* CREATION : 15.05.26 PNK
*-----------------------------------------------------------------------------------*/

void	Hardware_Init( void )
{
	System_Init();
	Vbl_Init();
	Video_Init();
	IKBD_Init();
}


/*-----------------------------------------------------------------------------------*
* FUNCTION : Hardware_DeInit( void )
* ACTION   : Hardware_DeInit
* CREATION : 15.05.26 PNK
*-----------------------------------------------------------------------------------*/

void	Hardware_DeInit( void )
{
	IKBD_DeInit();
	Video_DeInit();
	Vbl_DeInit();
	System_DeInit();
}


/*-----------------------------------------------------------------------------------*
* FUNCTION : Test_Loop( void )
* ACTION   : Test_Loop
* CREATION : 15.05.26 PNK
*-----------------------------------------------------------------------------------*/

void	Test_Loop( void )
{
	U32		lBase;
	void *	lpScreenMem;
	U16 *	lpPhysic;

	/* set to a 320x200 16 colour screen*/
	Video_SetResolution( 320, 200, eGRAPHIC_COLOURMODE_4PLANE, 320 );

	/* allocate screen compatible memory*/
	lpScreenMem = mMEMSCREENCALLOC( 32000L + 255L );

	if( lpScreenMem )
	{
		/* all screen buffers have to be aligned to nearest 256 bytes*/
		lBase       = (U32)lpScreenMem;
		lBase       += 255L;
		lBase      &= 0xFFFFFF00L;

		lpPhysic    = (U16*)lBase;

		Memory_Clear( 32000L, lpPhysic );

		Video_SetPalST( &gMyPalette[ 0 ] );
		Font_DrawDemo( lpPhysic );
		Video_SetPhysic( lpPhysic );

		/* wait for space to be pressed */
		while( !IKBD_GetKeyStatus(eIKBDSCAN_SPACE) )
		{
			IKBD_Update();
		}

		mMEMSCREENFREE( lpScreenMem );
	}
}


/*-----------------------------------------------------------------------------------*
* FUNCTION : Font_DrawDemo( U16 * apScreen )
* ACTION   : draws a title in the default font plus one line per palette colour
* CREATION : 15.05.26 PNK
*-----------------------------------------------------------------------------------*/

void	Font_DrawDemo( U16 * apScreen )
{
	char	lLine[ 16 ];
	U16		lColour;
	U16		lY;

	/* original single-colour printer (writes plane 0 only) */
	Font8x8_Print( "FONT8X8 DEMO - PRESS SPACE", apScreen, 8, 4 );

	/* coloured printer - one label per palette index 1..15 */
	for( lColour=1; lColour<16; lColour++ )
	{
		lLine[ 0 ] = 'C';
		lLine[ 1 ] = 'O';
		lLine[ 2 ] = 'L';
		lLine[ 3 ] = 'O';
		lLine[ 4 ] = 'U';
		lLine[ 5 ] = 'R';
		lLine[ 6 ] = ' ';
		lLine[ 7 ] = (char)('0' + (lColour / 10));
		lLine[ 8 ] = (char)('0' + (lColour % 10));
		lLine[ 9 ] = 0;

		lY = (U16)(20 + ((lColour - 1) * 11));
		Font8x8_PrintColour( lLine, apScreen, 8, lY, lColour );
	}
}


/* ################################################################################ */
