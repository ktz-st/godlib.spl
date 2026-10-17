#!/usr/bin/env python3
"""Keep James Boulton's VU graphics; precompute minimal row spans between states."""
from pathlib import Path
import struct,json,hashlib
from PIL import Image
root=Path(__file__).resolve().parent
src=root.parents[1]/'Atari_ST_Sources/ASM/Various/James Boulton/STF_DEMO'
a=root/'assets';a.mkdir(exist_ok=True)
original=(a/'STF_VU.DAT').read_bytes() if (a/'STF_VU.DAT').exists() else (src/'VU.DAT').read_bytes()
palette=(a/'PALETTE.BIN').read_bytes() if (a/'PALETTE.BIN').exists() else (src/'PALETTE.DAT').read_bytes()
assert len(original)==16*1200 and len(palette)==32
(a/'STF_VU.DAT').write_bytes(original);(a/'PALETTE.BIN').write_bytes(palette)
# Original state zero has a small central green bar. Add a truly blank idle state.
frames=bytes(1200)+original;(a/'FRAMES.BIN').write_bytes(frames)
spans=[]
for new in range(17):
 for old in range(17):
  changed=[y for y in range(150) if frames[new*1200+y*8:new*1200+y*8+8]!=frames[old*1200+y*8:old*1200+y*8+8]]
  first,last=(changed[0],changed[-1]) if changed else (0,-1)
  spans.extend([first*160,first*8,last-first+1])
(a/'SPANS.BIN').write_bytes(struct.pack('>'+str(len(spans))+'H',*spans))
words=struct.unpack('>16H',palette);pal=[((v>>s)&7)*255//7 for v in words for s in (8,4,0)]
im=Image.new('P',(17*16,150));im.putpalette(pal)
for state in range(17):
 pix=[]
 for y in range(150):
  p=struct.unpack_from('>4H',frames,state*1200+y*8)
  pix.extend(sum(((v>>(15-x))&1)<<j for j,v in enumerate(p)) for x in range(16))
 im.paste(Image.frombytes('P',(16,150),bytes(pix)),(state*16,0))
im.save(a/'bars.png',bits=4)
(a/'provenance.json').write_text(json.dumps({'author':'James Boulton','source':'ST Format Demo V1.0, (C) 1993 James Boulton','original_directory':str(src.relative_to(root.parents[1])),'original_vu_sha256':hashlib.sha256(original).hexdigest(),'original_palette_sha256':hashlib.sha256(palette).hexdigest(),'original_state_count':16,'original_state_size':1200,'original_dimensions':[16,150],'original_colour_planes':4,'added_state':0,'mapping':'output 0 blank; output 1..16 = original 0..15','span_record':'destination byte offset, source byte offset, row count; U16 big-endian','span_index':'(newLevel*17+oldLevel)*6'},indent=2)+'\n')
print('Imported original STF bars and palette; generated 17x17 row-transition table.')
