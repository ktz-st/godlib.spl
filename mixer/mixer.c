/*************************************************************************************
 * GodLib Example Progam Suite
 * 
 * Demonstrates audio mixer
 *
 * PINK 13.10.18
 *************************************************************************************
*/

/* ###################################################################################
#  INCLUDES
################################################################################### */

#ifndef dGODLIB_AUDIO_MIXER
#define dGODLIB_AUDIO_MIXER
#endif

#include	<godlib/audio/audio.h>
#include	<godlib/audio/amixer.h>
#include	<godlib/file/file.h>
#include	<godlib/font8x8/font8x8.h>
#include	<godlib/gemdos/gemdos.h>
#include	<godlib/ikbd/ikbd.h>
#include	<godlib/platform/platform.h>
#include	<godlib/screen/screen.h>
#include	<godlib/system/system.h>
#include	<godlib/vbl/vbl.h>
#include	<godlib/video/video.h>

/* ###################################################################################
#  PROTOTYPES
################################################################################### */

void	Hardware_Init( void );
void	Hardware_DeInit( void );

void	Test_Loop( void );

#define	dMIXER_BUFFER_SIZE	(8*1024)

U16				gMyPalette[ 16 ] =
{
	0x000,0xFFF,0xFFF,0xFFF,0xFFF,0xFFF,0xFFF,0xFFF,
	0xFFF,0xFFF,0xFFF,0xFFF,0xFFF,0xFFF,0xFFF,0xFFF
};

void	MixerBuffer_Render( U16 * apScreen, U16 aX, U16 aY, U16 aWidth, U16 aHeight );

/* ###################################################################################
#  CODE
################################################################################### */

/*-----------------------------------------------------------------------------------*
* FUNCTION : main( void )
* ACTION   : it begins  ...
* CREATION : 11.08.2018 PNK
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
* ACTION   : explicitly initialises platform and mixer services used by this example
* CREATION : 29.04.2026
*-----------------------------------------------------------------------------------*/

void	Hardware_Init( void )
{
	Platform_Init();
	File_Init();
	AudioMixer_Init();
	AudioMixer_Enable();
}


/*-----------------------------------------------------------------------------------*
* FUNCTION : Hardware_DeInit( void )
* ACTION   : explicitly shuts down mixer services before platform deinit
* CREATION : 29.04.2026
*-----------------------------------------------------------------------------------*/

void	Hardware_DeInit( void )
{
	AudioMixer_Disable();
	AudioMixer_DeInit();
	File_DeInit();
	Platform_DeInit();
}



/*-----------------------------------------------------------------------------------*
* FUNCTION : Test_Loop( void )
* ACTION   : Test_Loop
* CREATION : 11.08.2018 PNK
*-----------------------------------------------------------------------------------*/

void	Menu_Print( void )
{
	U16 *	lpScreen;

	lpScreen = Screen_GetpLogic();
	Font8x8_Print( "GodLib Mixer Example", lpScreen, 0, 0 );
	Font8x8_Print( "F1: Left", lpScreen, 0, 16 );
	Font8x8_Print( "F2: Right", lpScreen, 0, 24 );
	Font8x8_Print( "F3: Centre", lpScreen, 0, 32 );
	Font8x8_Print( "Space: Quit", lpScreen, 0, 48 );
	Font8x8_Print( "DMA: 25kHz  Sample: 12kHz", lpScreen, 0, 64 );

}

/*-----------------------------------------------------------------------------------*
* FUNCTION : Test_Loop( void )
* ACTION   : Test_Loop
* CREATION : 11.08.2018 PNK
*-----------------------------------------------------------------------------------*/

void	Test_Loop( void )
{
	char * lpSampleFileName = "voice.raw";
	sAudioDmaSound	lSound;

	Screen_Init( 320, 200, eGRAPHIC_COLOURMODE_4PLANE, eSCREEN_SCROLL_NONE );
	Video_SetPalST( &gMyPalette[ 0 ] );

	lSound.mBits = eAUDIO_BITS_8;
	lSound.mFreq = eAUDIO_FREQ_12;
	lSound.mLoopingFlag = 0;
	lSound.mStereoFlag = 0;
	lSound.mLength = File_GetSize(lpSampleFileName);
	lSound.mpSound = File_Load(lpSampleFileName);
	if( !lSound.mpSound )
	{
		GemDos_Cconws( "\033E\033fCould not load voice.raw\r\n" );
		GemDos_Cnecin();
		return;
	}

	Audio_MaximiseVolumeSigned( &lSound );
/*	Audio_ToggleSign( &lSound );*/

	AudioMixer_PlaySample( &lSound, eAMIXER_PAN_LEFT );

	for( ;; )
	{
		Screen_Update();
		Screen_Logic_ClearScreen();
		Menu_Print();
		MixerBuffer_Render( Screen_GetpLogic(), 0, 100, 256, 80 );

		IKBD_Update();
		if( IKBD_GetKbdBytesWaiting() )
		{
			U8 lKey = IKBD_PopKbdByte();

			if( eIKBDSCAN_F1 == lKey )
			{
				AudioMixer_PlaySample( &lSound, eAMIXER_PAN_LEFT );
			}
			else if( eIKBDSCAN_F2 == lKey )
			{
				AudioMixer_PlaySample( &lSound, eAMIXER_PAN_RIGHT );
			}
			else if( eIKBDSCAN_F3 == lKey )
			{
				AudioMixer_PlaySample( &lSound, eAMIXER_PAN_CENTRE );
			}
			else if( eIKBDSCAN_SPACE == lKey )
			{
				break;
			}
		}
	}


	/* unload sound samples */
	File_UnLoad(lSound.mpSound);
}

void	MixerBuffer_Render( U16 * apScreen, U16 aX, U16 aY, U16 aWidth, U16 aHeight )
{
	U8 * lpBuffer = AudioMixer_GetpBuffer();
	U32 lBufferSize = dMIXER_BUFFER_SIZE;
	U32 lChunkSize = (lBufferSize / aWidth) / 2;
	U16 lMaxH = ( aHeight >> 1 );
	U16	y0 = (aY)+( lMaxH ) - ( lMaxH >> 1 );
	U16	y1 = (aY)+( lMaxH ) + ( lMaxH >> 1 );
	U16 x;

	(void)apScreen;

	for( x = 0; x < aWidth; x++ )
	{
		U16 lChunkTotal0=0;
		U16 lChunkTotal1 = 0;
		sGraphicRect	lRect;
/*#ifdef dGODLIB_PLATFORM_ATARI*/
#if 1
		lChunkTotal0 = lpBuffer[ 0 ] >> 2;
		lChunkTotal1 = lpBuffer[ 1 ] >> 2;
		lpBuffer += lChunkSize;
		lpBuffer += lChunkSize;
#else
		{
			U16 i;
			for( i = 0; i < lChunkSize;i++ )
			{
				lChunkTotal0 += *lpBuffer++;
				lChunkTotal1 += *lpBuffer++;
			}
		}
		lChunkTotal0 /= (U16)lChunkSize;
		lChunkTotal1 /= (U16)lChunkSize;

		lChunkTotal0 *= lMaxH;
		lChunkTotal1 *= lMaxH;

		lChunkTotal0 >>= 9;
		lChunkTotal1 >>= 9;
#endif

		lRect.mX = aX + x;
		lRect.mWidth = 1;
		lRect.mY = y0 - lChunkTotal0;
		lRect.mHeight = lChunkTotal0 << 1;

		Screen_Logic_DrawBox_Clip( &lRect, 1 );

		lRect.mY = y1 - lChunkTotal1;
		lRect.mHeight = lChunkTotal1 << 1;

		Screen_Logic_DrawBox_Clip( &lRect, 1 );
	}
}


/* ################################################################################ */
