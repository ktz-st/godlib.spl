#!/usr/bin/env python3
"""Map all 12-bit PSG tone periods to 80 chromatic bands, C1 through G7."""
from pathlib import Path
import math
p=Path(__file__).resolve().parent
notes=[]
for period in range(4096):
 frequency=125000/max(1,period)
 midi=math.floor(69+12*math.log2(frequency/440)+0.5)
 notes.append(max(0,min(79,midi-24)))
(p/'assets/NOTES.BIN').write_bytes(bytes(notes))

# Eight-pixel phase for centered bars at X=120/152/184. MOVEP.L scatters
# one packed byte per plane while preserving both adjacent half-words.
raw=(p/'assets/FRAMES.BIN').read_bytes()
shifted=bytearray()
for i in range(0,len(raw),8):
 row=raw[i:i+8];shifted+=row[::2]+row[1::2]
(p/'assets/FRAMES8.BIN').write_bytes(shifted)
