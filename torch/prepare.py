"""Reuse the castle artwork: ABC2, eight STE colours, no dithering."""
from pathlib import Path
from PIL import Image
import hashlib,json,math,struct,sys
root=Path(__file__).resolve().parent
sys.path.insert(0,str(root.parent/'tools'))
from abc2_assets import convert,pack,rgb
source=root.parent/'water/assets/castle-source.png'
im=Image.open(source).convert('RGB').resize((320,200),Image.Resampling.LANCZOS)
words,indices,preview,meta=convert(im,planes=3,locks={7:0xfff})
def encode(c):return ((c>>1)&7)|((c&1)<<3)
dark=[]
for word in words:
 channels=[((((word>>s)&7)<<1)|((word>>s)>>3&1)) for s in (8,4,0)]
 dark.append(sum(encode((v+2)//4)<<s for v,s in zip(channels,(8,4,0))))
palette=dark+words
(root/'assets/IMAGE.BIN').write_bytes(pack(indices,320,200,4))
(root/'assets/PALETTE.BIN').write_bytes(struct.pack('>16H',*palette))
(root/'assets/HALF.BIN').write_bytes(struct.pack('>97H',*[math.isqrt(48*48-y*y) for y in range(-48,49)]))
(root/'assets/SINE.BIN').write_bytes(struct.pack('>256h',*[round(127*math.sin(i*2*math.pi/256)) for i in range(256)]))
preview.save(root/'assets/castle-8col.png')
meta.update({'source':str(source.relative_to(root.parent)),'file_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'radius':48,'dark_palette':[hex(v) for v in dark]})
(root/'assets/provenance.json').write_text(json.dumps(meta,indent=2)+'\n')
print('ABC2: 8 colours, 320x200; fourth plane reserved for light')
