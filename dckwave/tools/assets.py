#!/usr/bin/env python3
from pathlib import Path
from PIL import Image
import hashlib,json,math,struct

APP=Path(__file__).resolve().parents[1]
source=APP/'source/CASTLE.PI1';data=source.read_bytes()
assert len(data)==32034
# Fit the complete castle/lake composition into the 160-row stage.
native=b''.join(data[34+(y*200//160)*160:34+(y*200//160+1)*160] for y in range(160))
palette=data[2:34]
shifts=[round(8*math.sin(i*math.tau/256)) for i in range(256)]
assert min(shifts)==-8 and max(shifts)==8
(APP/'assets/PICTURE.BIN').write_bytes(native)
(APP/'assets/PALETTE.BIN').write_bytes(palette)
(APP/'assets/SHIFTS.BIN').write_bytes(bytes(x&255 for x in shifts)*3)
words=struct.unpack('>16H',palette)
rgb=[(((((w>>s)&7)<<1)|((w>>(s+3))&1))*17) for w in words for s in (8,4,0)]
idx=bytearray(320*160)
for y in range(160):
 for group in range(20):
  w=struct.unpack_from('>4H',native,y*160+group*8)
  for bit in range(16):idx[y*320+group*16+bit]=sum(((w[p]>>(15-bit))&1)<<p for p in range(4))
image=Image.frombytes('P',(320,160),bytes(idx));image.putpalette(rgb+[0]*(768-len(rgb)));image.save(APP/'source/CASTLE.png',bits=4)
manifest={'source':'water/assets/CASTLE.PI1, existing ABC2 STE 16-colour castle/lake','source_sha256':hashlib.sha256(data).hexdigest(),'picture_sha256':hashlib.sha256(native).hexdigest(),'viewport':[0,24,320,160],'source_row':'floor(y*200/160)','palette_words':[hex(w) for w in words],'used_indices':sorted(set(idx)),'hud_index':14,'amplitude':8,'phase_count':256,'row_phase_step':2,'shifts':shifts,'original_code':'DCK4/LCK1 TEXT $0CE0-$1004 generator; $1990-$19F8 runtime; ROXR/ROXL selected planes','adaptation':'No generated or cached frames. Incremental per-page shifts with source-edge refill; direct source recomposition for jumps >2 px. No SR writes, blitter or raster interrupts.'}
(APP/'assets/source.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('Prepared 25600-byte picture, 32-byte palette, 768-byte wave table.')
