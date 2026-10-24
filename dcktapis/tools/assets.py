#!/usr/bin/env python3
from pathlib import Path
from PIL import Image
import hashlib,json,struct

APP=Path(__file__).resolve().parents[1]
picture=(APP/'source/TAPIS3_4.PI1').read_bytes();col=(APP/'source/TAPIS.COL').read_bytes()
assert len(picture)==32034 and len(col)==8800
rows=[col[i:i+32] for i in range(0,len(col),32)]
assert rows[0]==rows[1]==picture[2:34]
assert all(any(row) for row in rows[:15]) and not any(col[15*32:])
# Record zero is the saved picture palette. Records 1..14 are the complete
# original cyclic pattern; 15..274 are unused zero-filled capacity.
cycle=b''.join(rows[1:15]);native=picture[34:]
(APP/'assets/PICTURE.BIN').write_bytes(native)
(APP/'assets/PALETTES.BIN').write_bytes(cycle)
idx=bytearray(64000)
for y in range(200):
 for x in range(20):
  words=struct.unpack_from('>4H',native,y*160+x*8)
  for b in range(16):idx[y*320+x*16+b]=sum(((words[p]>>(15-b))&1)<<p for p in range(4))
assert 1 not in idx
for y in [64,65,66,67,68,69,70,71,80,81,82,83,84,85,86,87,*range(184,200)]:
 assert not any(idx[y*320:(y+1)*320]),y
def image(palette):
 rgb=[(((((w>>s)&7)<<1)|((w>>(s+3))&1))*17) for w in struct.unpack('>16H',palette) for s in (8,4,0)]
 im=Image.frombytes('P',(320,200),bytes(idx));im.putpalette(rgb+[0]*(768-len(rgb)));return im
image(rows[0]).save(APP/'source/TAPIS.png',bits=4)
manifest={'picture':'DCK/extracted/pi1/dessin/TAPIS3_4.PI1','picture_source_sha256':hashlib.sha256(picture).hexdigest(),'native_sha256':hashlib.sha256(native).hexdigest(),'palette_source':'DCK/extracted/disk-b/PALETTE/TAPIS.COL','palette_source_sha256':hashlib.sha256(col).hexdigest(),'runtime_palette_sha256':hashlib.sha256(cycle).hexdigest(),'col_records':275,'cycle_records':list(range(1,15)),'unused_zero_records':[15,274],'record_0':'saved palette, identical to record 1 and PI1 header','used_indices':sorted(set(idx)),'hud_index':1,'original_picture_unchanged':True,'original_palettes_unchanged':True,'original_code':'DCK4/LCK1 TEXT $2C4A / $2E16 / $2EA4 palette base and phasing, $2F2A-$31BA raster palette reloads','adaptation':'Full original 320x200 bitmap, 14 complete palette records played temporally in GodLib VBL; no HBL/raster/overscan. Legends added only to original black rows.'}
(APP/'assets/source.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('Prepared unchanged 32000-byte TAPIS bitmap and 14 x 32-byte palettes.')
