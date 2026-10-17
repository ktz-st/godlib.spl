"""Pack the unchanged ABC2 STE coast as 20 contiguous 16-pixel columns."""
from pathlib import Path
import math,struct
r=Path(__file__).resolve().parents[1];b=(r/'assets/COAST.PI1').read_bytes()
assert len(b)==32034 and b[:2]==b'\0\0'
(r/'assets/PALETTE.BIN').write_bytes(b[2:34])
raw=b''.join(b[34+y*160+x*8:42+y*160+x*8] for x in range(20) for y in range(200))
assert len(raw)==32000
for x in range(20):
 for y in range(200):assert raw[x*1600+y*8:x*1600+y*8+8]==b[34+y*160+x*8:42+y*160+x*8]
(r/'assets/COLUMNS.BIN').write_bytes(raw)
lut=[round(amp*math.sin(i*math.tau/256)) for amp in (4,10,16) for i in range(256)]
(r/'assets/SINE.BIN').write_bytes(struct.pack('>768h',*lut))
