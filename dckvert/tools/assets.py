from pathlib import Path
from PIL import Image
import json,hashlib
r=Path(__file__).resolve().parents[1];im=Image.open(r/'source/BIG.png');src=(r/'source/BIG.PI1').read_bytes();font=bytearray()
for glyph in range(49):
 for y in range(32):
  for group in range(3):
   size=16 if group<2 else 8
   for plane in range(4):
    v=0
    for bit in range(size):
     c=im.getpixel((glyph%8*40+group*16+bit,glyph//8*32+y))if glyph<48 else 0
     v|=((c>>plane)&1)<<(size-1-bit)
    font.extend(v.to_bytes(size//8,'big'))
(r/'assets/FONT.BIN').write_bytes(font);(r/'assets/PALETTE.BIN').write_bytes(src[2:34])
cells={c:i for i,c in enumerate('ABCDEFGHIJKLMNOPQRSTUVWXYZ')};cells.update({'!':26,"'":27,'(':28,')':29,'-':30,'.':31,'?':32,':':33,',':44});cells.update({str(n):34+n for n in range(10)})
texts=['GODLIB VERTICAL SCROLLER!   ', 'ATARI ST - BIG FONT - FULL COLOUR!   ', 'DCK LIVES AGAIN! ASM AND ONE PIXEL PER FRAME!   ']
(r/'assets/text.inc').write_text('\n'.join('Vert_Text%d:\n        dc.b '%i+','.join(str(cells.get(c,48))for c in text)+',255\n        even'for i,text in enumerate(texts))+'\n')
(r/'assets/source.json').write_text(json.dumps({'source':'DCK disk B FONTES/BIG.PC1, lossless PI1','sha256':hashlib.sha256(src).hexdigest(),'glyph':[40,32],'row_bytes':20,'gap_rows':8,'column_x':[48,144,240],'window_y':28,'window_height':144,'texts':texts},indent=2)+'\n')
