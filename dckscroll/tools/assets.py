from pathlib import Path
from PIL import Image
import struct,math,hashlib,json
r=Path(__file__).resolve().parents[1];src=r/'source/BIG.PI1';im=Image.open(r/'source/BIG.png')
# Original atlas: 8 columns x 6 rows, 40x32. Append a blank space glyph.
# Explicit original cell coordinates (unused cells stay unavailable).
cells={c:i for i,c in enumerate('ABCDEFGHIJKLMNOPQRSTUVWXYZ')}
cells.update({'!':26,"'":27,'(':28,')':29,'-':30,'.':31,'?':32,':':33,',':44})
for n in range(10):cells[str(n)]=34+n
font=bytearray()
for i in range(49):
 for col in range(5):
  for y in range(32):
   v=[im.getpixel((i%8*40+col*8+x,i//8*32+y))if i<48 else 0 for x in range(8)]
   font.extend(sum(((v[x]>>p)&1)<<(7-x)for x in range(8))for p in range(4))
(r/'assets/FONT.BIN').write_bytes(font);(r/'assets/PALETTE.BIN').write_bytes(src.read_bytes()[2:34])
paths=[[round(31+8*math.sin(x*2*math.pi/40))for x in range(40)], [round(92-13*(1-((x-19.5)/19.5)**2))for x in range(40)], [round(143+8*(1-4*abs((x/20)%1-.5)))for x in range(40)]]
(r/'assets/PATHS.BIN').write_bytes(b''.join(struct.pack('>h',v)for path in paths for v in path))
texts=['   GODLIB MEETS DCK - THREE COLOUR SCROLLERS ON THE ATARI ST!   ', '   BIG FONT - GENERATED 68000 CODE - NO BLITTER REQUIRED!   ', '   SINE ARCH AND ZIGZAG - THE PIXEL BOYS AND DCK LIVE AGAIN!   ']
(r/'assets/text.inc').write_text('\n'.join('Dck_Text%d:\n        dc.b '%i+','.join(str(cells.get(c,48))for c in text)+',255\n        even'for i,text in enumerate(texts))+'\n')
(r/'assets/source.json').write_text(json.dumps({'source':'DCK disk B / FONTES/BIG.PC1 (lossless PI1)' ,'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'glyph_size':[40,32],'glyph_storage':'5 columns x 32 rows x 4 planar bytes, MOVEP-ready','curves':paths,'texts':texts},indent=2)+'\n')
