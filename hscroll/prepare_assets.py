"""Prepare a 640x200 four-plane panorama: 16 big-endian ST palette words + pixels."""
from pathlib import Path
import struct
from PIL import Image
root=Path(__file__).resolve().parent
image=Image.open(root/'assets/panorama-original.png').convert('RGB').resize((640,200),Image.Resampling.LANCZOS)
reduced=image.quantize(colors=14,method=Image.Quantize.MEDIANCUT)
colours=reduced.getpalette()[:42]
words=[0]
for i in range(0,42,3):
 w=sum(round(colours[i+j]*7/255)<<shift for j,shift in enumerate((8,4,0)))
 if w not in words and w!=0x777: words.append(w)
for w in (0x111,0x222,0x333,0x444,0x555,0x666):
 if len(words)>=15: break
 if w not in words: words.append(w)
while len(words)<15: words.append(words[-1])
words=words[:15]+[0x777]
pal=Image.new('P',(1,1));pal.putpalette([round(((w>>s)&7)*255/7) for w in words for s in (8,4,0)]+[0]*720)
indexed=image.quantize(palette=pal,dither=Image.Dither.FLOYDSTEINBERG)
pixels=indexed.tobytes();assert max(pixels)<16
out=bytearray(struct.pack('>16H',*words))
for y in range(200):
 for x in range(0,640,16):
  for p in range(4):
   out+=struct.pack('>H',sum(((pixels[y*640+x+i]>>p)&1)<<(15-i) for i in range(16)))
assert len(out)==64032
for y in range(200):
 for x in range(640):
  planes=struct.unpack_from('>4H',out,32+y*320+(x//16)*8)
  assert sum(((planes[p]>>(15-x%16))&1)<<p for p in range(4))==pixels[y*640+x]
(root/'PANORAMA.BIN').write_bytes(out)
indexed.convert('RGB').save(root/'assets/panorama-st.png')
print('PANORAMA.BIN: 640x200, 16 ST colours, 64032 bytes; all pixels verified')
