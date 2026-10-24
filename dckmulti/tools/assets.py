from pathlib import Path
from PIL import Image
import json,struct,hashlib
r=Path(__file__).resolve().parents[1];cfg=json.loads((r/'source/config.json').read_text());im=Image.open(r/'source/ESCALI.png');font=bytearray()
# Atlas cells 0..25: A-Z; 26..35: 0-9. Cell 36 is an appended blank.
for glyph in range(37):
 for col in range(2):
  for y in range(16):
   pixels=[im.getpixel((glyph%20*16+col*8+x,glyph//20*16+y))if glyph<36 else 0 for x in range(8)]
   font.extend(sum(((pixels[x]>>p)&1)<<(7-x)for x in range(8))for p in range(4))
(r/'assets/FONT.BIN').write_bytes(font)
(r/'assets/PALETTE.BIN').write_bytes((r/'source/ESCALI.PI1').read_bytes()[2:34])
cells={c:i for i,c in enumerate('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')}
text=[]
for n,s in enumerate(cfg['texts']):
 # A rightward incoming stream consumes characters and glyph slices in reverse
 # order, so the visible text retains its normal left-to-right spelling.
 if cfg['directions'][n]<0:s=s[::-1]
 text.append('HS_Text%d:\n        dc.b '%n+','.join(str(cells.get(c,36))for c in s)+',255\n        even')
(r/'assets/text.inc').write_text('\n'.join(text)+'\n')
(r/'assets/config.inc').write_text('HS_LANES equ %d\n'%cfg['lanes']+'HS_Blank equ 36*128\nHS_StateSize equ 24\n')
(r/'assets/tables.inc').write_text('HS_TextPointers: dc.l '+','.join('HS_Text%d'%i for i in range(cfg['lanes']))+'\nHS_YOffsets: dc.w '+','.join(str(y*160)for y in cfg['y'])+'\nHS_Periods: dc.w '+','.join(map(str,cfg['periods']))+'\nHS_Directions: dc.w '+','.join(map(str,cfg['directions']))+'\n')
(r/'assets/source.json').write_text(json.dumps(dict(cfg,source='DCK disk B FONTES/ESCALI.PC1',source_sha256=hashlib.sha256((r/'source/ESCALI.PI1').read_bytes()).hexdigest(),glyph_size=[16,16],font_bytes=len(font)),indent=2)+'\n')
