"""Reuse GodLib artwork/fonts/twinkles; ABC2 STE palettes, no dithering."""
from pathlib import Path
import sys,struct,json,hashlib
from PIL import Image,ImageOps
r=Path(__file__).resolve().parent
sys.path.insert(0,str(r.parent/'tools'))
from abc2_assets import convert,pack,rgb
locks={0:0,12:0x159,13:0x6be,14:0xfc0,15:0xfff}
sources=[r.parent/'water/assets/castle-source.png',r.parent/'wipe/assets/forest.png']
for name,source in zip(('CASTLE','FOREST'),sources):
 image=Image.new('RGB',(320,200));image.paste(ImageOps.fit(Image.open(source).convert('RGB'),(320,168)),(0,0))
 words,idx,preview,meta=convert(image,locks=locks)
 idx[168*320:]=[0]*(32*320)
 # One fine line separates the caption panel from the scene.
 idx[170*320:171*320]=[13]*320
 (r/f'assets/{name}.PI1').write_bytes(b'\0\0'+struct.pack('>16H',*words)+pack(idx,320,200))
 preview.putdata([rgb(words[i])for i in idx]);preview.save(r/f'assets/{name.lower()}.png')
 meta.update(source=str(source.relative_to(r.parent)),source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),footer='black from row 168, cyan separator 170, script text 178, controls 192')
 (r/f'assets/{name.lower()}.json').write_text(json.dumps(meta,indent=2)+'\n')
def unpack(raw,w,h,planes=4):
 out=[]
 for y in range(h):
  for x in range(0,w,16):
   vals=struct.unpack_from('>'+str(planes)+'H',raw,(y*w//16+x//16)*planes*2)
   out.extend(sum(((v>>(15-b))&1)<<p for p,v in enumerate(vals))for b in range(16))
 return out
font=(r.parent/'font/gfx/FONT6X6.PI1').read_bytes()
(r/'assets/FONT.BIN').write_bytes(pack([15 if n else 0 for n in unpack(font[34:],320,200)],320,200))
# Existing three 16x16 twinkle frames: preserve mask, recolour into shared slots.
stars=(r.parent/'spritemask/assets/STARS.BIN').read_bytes();result=bytearray()
for frame in range(3):
 raw=stars[frame*160:(frame+1)*160];idx=unpack(raw[32:],16,16)
 colours=sorted(set(idx)-{0});mapping={c:([12,13,15][-len(colours):])[i]for i,c in enumerate(colours)}
 result+=raw[:32]+pack([mapping.get(c,0)for c in idx],16,16)
(r/'assets/STAR.BIN').write_bytes(result)
