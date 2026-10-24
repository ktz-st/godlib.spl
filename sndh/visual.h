#ifndef SNDH_VISUAL_H
#define SNDH_VISUAL_H
#include <godlib/base/base.h>
extern volatile U8 gPsgRegisters[11];
extern U16 gPsgBarsPalette[16];
extern U16 gPsgLevels[3],gPsgEnvelope[3];
extern U8 gPsgBands[80];
extern void (*gSndVisPlay)(void);
extern volatile U16 gSndVisRaster;
void PsgVis_Replay(void);
void PsgVis_Snapshot(void);
void PsgVis_Update(void);
void PsgBars_Draw(void *screen,const U16 *levels,U16 *previous);
void PsgSpectrum_Draw(void *screen,const U8 *levels,U8 *previous);
extern U16 gPsgPeriods[3],gPsgToneLevels[3],gPsgNotes[3],gPsgNoteSerial[3];
extern U8 gPianoKeys[80];
extern U16 gRingAges[12],gScopeParams[6];
void PsgExtra_Init(void);
void PsgExtra_Update(void);
void PsgPiano_Init(void *screen);
void PsgPiano_Draw(void *screen,const U8 *keys,U8 *previous);
void PsgScope_Prepare(void);
void PsgScope_Draw(void *screen,const U16 *params,U16 *previous);
void PsgCircles_Draw(void *screen,const U16 *ages,U16 *previous);
void PsgOrgan_Init(void *screen);
void PsgOrgan_Update(const U16 *levels);
extern U8 gPsgHistogram[16];
void PsgHistogram_Reset(void);
void PsgHistogram_Update(void);
void PsgHistogram_Draw(void *screen,const U8 *levels,U8 *previous);
extern U16 gPsgDckLevels[3],gPsgDckPalette[16];
typedef void (*fPsgDckDraw)(void *,const U16 *,U16 *);
extern fPsgDckDraw gPsgDckDraw[4];
void PsgDck_Reset(void);
void PsgDck_Update(void);
#endif
