"""Offline word-interleaved preshifts and small cyclic wave lookup tables."""
from pathlib import Path
import math,struct
root=Path(__file__).resolve().parents[1]
b=(root/'assets/COAST.PI1').read_bytes();assert len(b)==32034 and b[:2]==b'\0\0'
cache=bytearray();sine=[round(16*math.sin(i*math.tau/256)) for i in range(256)]
for y in range(200):
 planes=[int.from_bytes(b'\0\0'+b''.join(b[34+y*160+g*8+p*2:36+y*160+g*8+p*2] for g in range(20))+b'\0\0','big') for p in range(4)]
 for fine in range(16):
  shifted=[((v<<fine)&((1<<352)-1)).to_bytes(44,'big') for v in planes]
  for g in range(22):
   for p in range(4):cache+=shifted[p][g*2:g*2+2]
assert len(cache)==563200
(root/'assets/PRESHIFT.BIN').write_bytes(cache)
(root/'assets/PALETTE.BIN').write_bytes(b[2:34])
lut=[]
for amp in (0,4,8,16):
 for phase in range(768):
  dx=0 if not amp else sine[phase&255]//(16//amp)
  start=16-dx;lut.append((start&15)*176+(start>>4)*8)
lut += [0xffff]*768
(root/'assets/LOOKUP.BIN').write_bytes(struct.pack('>3840H',*lut))
