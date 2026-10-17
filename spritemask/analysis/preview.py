"""Rebuild the palette-accurate animation preview from the actual assets."""
from pathlib import Path
from PIL import Image
import struct
r=Path(__file__).resolve().parents[1]
scene=Image.open(r/'assets/scene.png');moon=Image.open(r/'assets/moon.png')
mask=(r/'assets/FORE_REF.BIN').read_bytes()
fg=[(mask[y*40+x//8]>>(7-x%8))&1 for y in range(200)for x in range(320)]
bg=list(scene.get_flattened_data());mp=list(moon.get_flattened_data())
starpos=list(struct.iter_unpack('>3H',(r/'assets/STARPOS.BIN').read_bytes()))
def unpack(data):
 return [sum(((int.from_bytes(data[(j//16)*8+p*2:][:2],'big')>>(15-(j%16)))&1)<<p for p in range(4))for j in range(256)]
starbytes=(r/'assets/STARS.BIN').read_bytes();stars=[unpack(starbytes[i*160+32:(i+1)*160])for i in range(12)]
path=list(struct.iter_unpack('>hh',(r/'assets/PATH.BIN').read_bytes()));frames=[]
for frame in range(0,len(path),6):
 x,y=path[frame];indices=bg.copy()
 for starid,(px,py,offset) in enumerate(starpos):
  phase=(frame+offset)%192
  f=0 if phase<8 else 1 if phase<16 else 2 if phase<24 else 1 if phase<32 else 0
  for j,c in enumerate(stars[starid*3+f]):
   if c:indices[(py+j//16)*320+px+j%16]=c
 for sy in range(48):
  for sx in range(48):
   xx=x+sx;yy=y+sy;c=mp[sy*48+sx]
   if 0<=xx<320 and 0<=yy<200 and c and not fg[yy*320+xx]:indices[yy*320+xx]=c
 im=Image.new('P',(320,200));im.putpalette(scene.getpalette());im.putdata(indices)
 frames.append(im.resize((640,400),Image.Resampling.NEAREST))
frames[0].save(r/'analysis/moon.gif',save_all=True,append_images=frames[1:],duration=120,loop=0,optimize=False,disposal=2)
strip=Image.new('RGB',(3200,400))
for i,index in enumerate([3,25,50,72,len(frames)-1]):strip.paste(frames[index].convert('RGB'),(i*640,0))
strip.save(r/'analysis/preview.png')
