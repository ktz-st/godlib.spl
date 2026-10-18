#ifndef IRIS_H
#define IRIS_H
#include <godlib/graphic/graphic.h>
/* Example-local, fixed 320x200 four-plane screens, 160-byte stride.
   Span endpoints are inclusive; left > right means an empty row. */
typedef struct { S16 left,right; } sIrisSpan;
extern sIrisSpan gIrisSpans[200];
extern S16 gIrisX[7],gIrisY[7];
extern const S16 Iris_Sine[1920];
extern const U8 Iris_Image[],Iris_Image2[];
extern const U16 Iris_Palette[],Iris_Palette2[];
/* OR horizontal spans into bitplane 3 only. a0 = VRAM, a1 = 200 spans. */
void Iris_Fill(void *screen,const sIrisSpan *spans);
void Iris_Prepare(S16 h,U16 angle);
#endif
