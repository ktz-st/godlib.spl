"""Offline transform coefficients only; all scanlines are drawn at runtime."""
from pathlib import Path
import math,struct
root=Path(__file__).resolve().parent
out=bytearray()
for f in range(256):
 angle=2*math.pi*f/256
 cell=52+20*math.sin(2*angle)
 for a,b in [(math.cos(angle)/cell,math.sin(angle)/cell),(-math.sin(angle)/cell,math.cos(angle)/cell)]:
  # Tiny positive derivative represents exactly horizontal boundaries safely.
  if abs(a)<1/65536:a=1/65536
  sign=1 if a>0 else -1
  a,b=abs(a),b*sign
  c=.37*sign-160*a-56*b
  spacing=round(256/a);step=round(-256*b/a)
  raw=round(-c*spacing)
  first=raw%spacing
  parity=(math.floor(c)+(1 if sign<0 else 0))&1
  out+=struct.pack('>iiiH',first,step,spacing,65535 if parity else 0)
(root/'assets/PARAMS.BIN').write_bytes(out)
print(len(out),'bytes of transform coefficients; no pre-rendered frames')
