"""Offline affine coefficients and span commands; pixels are drawn at runtime."""
from pathlib import Path
import math,struct
root=Path(__file__).resolve().parent
out=bytearray()
for f in range(128):
 angle=2*math.pi*f/128
 cell=84+28*math.sin(2*angle)
 for a,b in [(math.cos(angle)/cell,math.sin(angle)/cell),(-math.sin(angle)/cell,math.cos(angle)/cell)]:
  # Tiny positive derivative represents exactly horizontal boundaries safely.
  if abs(a)<1/65536:a=1/65536
  sign=1 if a>0 else -1
  a,b=abs(a),b*sign
  c=.37*sign-160*a-48*b
  spacing=round(256/a);step=round(-256*b/a)
  raw=round(-c*spacing)
  first=raw%spacing
  parity=(math.floor(c)+(1 if sign<0 else 0))&1
  out+=struct.pack('>iiiH',first,step,spacing,65535 if parity else 0)
(root/'assets/PARAMS.BIN').write_bytes(out)
print(len(out),'bytes of transform coefficients; no pre-rendered frames')

# Span commands, not images: signed jump offset and a partial-word XOR mask.
# Positive jump offsets terminate a row; the renderer fills its remainder.
params=list(struct.iter_unpack('>iiiH',out))
commands=bytearray();offsets=[];maximum=0
for f in range(128):
 offsets.append(len(commands))
 for y in range(96):
  edges=[];colour=0
  for first,step,spacing,polarity in params[2*f:2*f+2]:
   raw=first+y*step;n=raw//spacing;edge=raw%spacing
   colour^=polarity^(65535 if n&1 else 0)
   while edge<320*256:
    x=(edge+255)//256
    if x<320:edges.append(x)
    edge+=spacing
  commands+=struct.pack('>H',colour)
  word=0
  for x in sorted(edges):
   newword=x//16
   commands+=struct.pack('>hH',-4*(newword-word),65535>>(x&15))
   word=newword
  commands+=struct.pack('>hH',1,0)
  maximum=max(maximum,len(edges))
(root/'assets/SPANS.BIN').write_bytes(commands)
(root/'assets/OFFSETS.BIN').write_bytes(struct.pack('>'+str(len(offsets))+'I',*offsets))
print(len(commands),'bytes of span geometry;',maximum,'boundaries per row maximum')
