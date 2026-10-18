"""Compile the actual SuperHex bg_render/bg_span on the host; compare all frames.
The original 246-row result is cropped by 23 rows to the 200-row viewport.
"""
from pathlib import Path
import tempfile,subprocess,sys,struct,math,json,hashlib
root=Path(__file__).resolve().parents[1]
source=(root.parents[1]/'superhex_ste/src/main.c').read_text()
part=source[source.index('static void bg_span('):source.index('static void bg_init(')]
sine=[max(-16384,min(16383,round(math.sin(2*math.pi*i/1536)*16384)))for i in range(1920)]
code='''#include <stdint.h>
#include <stdio.h>
#include <string.h>
typedef int16_t s16;typedef uint16_t u16;typedef int32_t s32;
#define BG_W 20
#define BG_H 246
#define BG_CY 123
#define BG_FR 9840
#define CX 160
#define SCR_W 320
#define ANG_SECTOR 256
#define ANG_FULL 1536
static u16 angwrap(s32 a){while(a<0)a+=1536;while(a>=1536)a-=1536;return a;}
static const s16 sintab[1920]={'''+','.join(map(str,sine))+'};\n'+part+'''
int main(void){u16 fr[BG_W*BG_H];for(int f=0;f<32;f++){
bg_render(fr,f*8+4);for(int y=23;y<223;y++)for(int w=0;w<20;w++){
u16 v=fr[y*20+w];putchar(v>>8);putchar(v&255);}}return 0;}
'''
with tempfile.TemporaryDirectory(prefix='wedges-original-') as td:
 p=Path(td);(p/'oracle.c').write_text(code)
 subprocess.run(['cc','-O2','-fwrapv',str(p/'oracle.c'),'-o',str(p/'oracle')],check=True)
 expected=subprocess.check_output([str(p/'oracle')])
actual=(root/'assets/FRAMES.BIN').read_bytes();assert len(expected)==256000 and actual==expected
report={'method':'Actual bg_span/bg_render extracted from SuperHex source, host-compiled with fixed-width original types, original 320x246 output cropped at row 23','original_functions_sha256':hashlib.sha256(part.encode()).hexdigest(),'frames':32,'bytes_compared':len(actual),'all_equal':True,'frames_sha256':hashlib.sha256(actual).hexdigest()}
(root/'analysis/tables-verification.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS: all 32 masks equal original SuperHex bg_render (256000 bytes)')
