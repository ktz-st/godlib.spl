#ifndef CRT_EXAMPLE_H
#define CRT_EXAMPLE_H
#include <godlib/base/base.h>
typedef struct { S16 x[11],y;S16 band;U16 scan; } sCrtHistory;
extern const U8 Crt_Image[];extern const U16 Crt_Palette[];
extern S16 gCrtX[11],gCrtY,gCrtBand;
extern U16 gCrtScan;
extern U8 *gCrtScreen;extern sCrtHistory *gCrtHistory;
extern const U8 Crt_Source[],Crt_Source2[],Crt_Image2[];
extern const U16 Crt_Palette2[],Crt_TvCount,Crt_TvPalettes[],Crt_TvPalettes2[];
void Crt_Render(void);
void Crt_TvRender(void);
#endif
