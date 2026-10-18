#ifndef IRIS_H
#define IRIS_H
#include <godlib/graphic/graphic.h>
/* Example-local, fixed 320x200 four-plane screens, 160-byte stride.
   Span endpoints are inclusive; left > right means an empty row. */
typedef struct { S16 left,right; } sIrisSpan;
typedef struct { S32 xL,xR,dxL,dxR; U16 count; } sIrisRun;
extern sIrisSpan gIrisSpans[200];
extern S16 gIrisX[7],gIrisY[7];
extern const S16 Iris_Sine[1920];
extern U8 Iris_Image[],Iris_Image2[]; /* startup adds legends in these writable assets */
extern const U16 Iris_Palette[],Iris_Palette2[];
void Iris_Prepare(S16 h,U16 angle);
void Iris_Scan(sIrisSpan *spans,const sIrisRun *runs,S16 first,S16 last);
void Iris_CopyRows(void *screen,const void *source,U16 row,U16 count);
void Iris_Delta(void *screen,U16 *history);
void Iris_Restore(void *screen,const void *background);
void Iris_WhiteLine(void *screen,const sGraphicBox *line);
#endif
