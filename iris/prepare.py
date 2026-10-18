"""Existing RGB artwork -> ABC2 STE, seven image colours + reserved white edge.
No dithering. A duplicated forced-black slot 7 is folded into slot 0.
The separate mask plane selects a black palette bank, not alpha blending.
"""
from pathlib import Path
from PIL import Image,ImageOps
import sys,math,struct,json,hashlib
root=Path(__file__).resolve().parent
sys.path.insert(0,str(root.parent/'tools'))
from abc2_assets import convert,pack
sources=[root.parent/'water/assets/castle-source.png',root.parent/'wipe/assets/forest.png']
for i,source in enumerate(sources):
 im=ImageOps.fit(Image.open(source).convert('RGB'),(320,200),method=Image.Resampling.LANCZOS)
 words,idx,preview,meta=convert(im,planes=3,locks={0:0,7:0})
 assert words[0]==words[7]==0
 idx=[0 if n==7 else n for n in idx];assert max(idx)<=6
 words[7]=0xfff;palette=words+[0]*7+[0xfff]
 suffix=''if i==0 else '2'
 (root/f'assets/IMAGE{suffix}.BIN').write_bytes(pack(idx,320,200,4))
 (root/f'assets/PALETTE{suffix}.BIN').write_bytes(struct.pack('>16H',*palette))
 preview.save(root/f'assets/preview{suffix}.png')
 meta.update(source=str(source.relative_to(root.parent)),source_file_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),reserved={'7':'white edge only, never in source','8..14':'black shutter','15':'white edge under shutter'},used_image_indices=sorted(set(idx)))
 (root/f'assets/provenance{suffix}.json').write_text(json.dumps(meta,indent=2)+'\n')
values=[max(-16384,min(16383,round(math.sin(2*math.pi*i/1536)*16384))) for i in range(1920)]
(root/'assets/SINE.S').write_text('; SuperHex Q14 sine: 1536 steps plus cosine guard.\n'+''.join('        dc.w '+','.join(map(str,values[i:i+12]))+'\n'for i in range(0,len(values),12)))
