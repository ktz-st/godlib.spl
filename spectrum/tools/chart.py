"""Generate an SPU test card using every STE RGB colour (512 after ST reduction)."""
from pathlib import Path
from PIL import Image,ImageDraw
import struct,json
r=Path(__file__).resolve().parents[1]
def word(rr,gg,bb):
 return sum(((v>>1)|((v&1)<<3))<<s for v,s in zip((rr,gg,bb),(8,4,0)))
plane=bytearray(32000);palette=[];labels=Image.new('1',(320,200));d=ImageDraw.Draw(labels)
d.text((65,8),'SPECTRUM 512 / 4096',fill=1)
d.text((25,176),'1: ST   2: STE   SPACE: RASTERS',fill=1)
d.text((42,188),'4096 COLOUR TEST   ESC: EXIT',fill=1)
seen=set()
for y in range(200):
 rowpal=[0]*48;rowpal[15]=rowpal[31]=rowpal[47]=0xfff
 for x in range(320):
  if 32<=y<160:
   row=y-32;c=(x//10)&15
  else:c=15 if labels.getpixel((x,y)) else 0
  off=y*160+(x//16)*8;mask=0x8000>>(x&15)
  for p in range(4):
   if c&(1<<p):
    v=struct.unpack_from('>H',plane,off+p*2)[0]|mask;struct.pack_into('>H',plane,off+p*2,v)
 if 32<=y<160:
  row=y-32
  for c in range(16):
   a=word(c,row&15,(row//16)*2);b=word(c,row&15,(row//16)*2+1)
   rowpal[c]=rowpal[16+c]=a;rowpal[32+c]=b;seen|={a,b}
 if y:palette+=rowpal
assert len(seen)==4096 and len({v&0x777 for v in seen})==512
(r/'assets/CHART.SPU').write_bytes(plane+struct.pack('>9552H',*palette))
(r/'assets/CHARTPIX.BIN').write_bytes(plane)
(r/'assets/CHARTSTE.BIN').write_bytes(struct.pack('>9552H',*palette))
(r/'assets/CHARTST.BIN').write_bytes(struct.pack('>9552H',*(v&0x777 for v in palette)))
