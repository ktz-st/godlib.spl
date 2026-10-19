#!/usr/bin/env python3
"""Make standalone BFB assets from GodLib's built-in 8x8 font."""
from pathlib import Path
import re,struct,sys
root=Path(__file__).resolve().parent;god=root.parents[1]/'godlib'
sys.path.insert(0,str(god/'tools/toolbase'))
import toolbase as t
raw=bytes(int(v,16)for v in re.findall(r'0x([0-9A-Fa-f]{2})',(god/'font8x8/fontdata.c').read_text()))
for name,colour in [('NORMAL.BFB',10),('ACTIVE.BFB',15)]:
 frames=[]
 for c in range(32,127):
  pixels=[0]*128;mask=[True]*128
  for y in range(8):
   for x in range(8):
    if raw[(c-32)*8+y]&(0x80>>x):pixels[y*16+x]=colour;mask[y*16+x]=False
  frames.append(t.planar_sprite(16,8,4,4,pixels,mask))
 data=bytearray(t.serialize_bfb(frames,t.SpriteDef(font=True,charfirst=32,charlast=126,spacewidth=8)));data[10]=0
 offset=struct.unpack_from('>I',data,28)[0]
 for i in range(95):struct.pack_into('>4H',data,offset+i*8,0,0,7,7)
 struct.pack_into('>2H',data,12,8,8);(root/'assets'/name).write_bytes(data)
print('Prepared fixed-width GodLib 8x8 BFBs')
