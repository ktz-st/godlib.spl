#ifndef RASTERS_H
#define RASTERS_H
#include <godlib/base/base.h>
/* Next Timer B delay (line gap minus one), padding, then ST colour zero. */
typedef struct { U8 mDelay,mPad; U16 mColour; } sRasterStep;
extern U16 gRasterLut[64],gRasterPalette[16];
extern U16 gRasterAnimate,gRasterSpeed,gRasterPhase,gRasterFramePhase;
extern volatile U16 gRasterEnabled;
void Raster_Init(void);
void Raster_DeInit(void);
#endif
