"""Reuse the water example's palette and ONLY the castle above the lake."""
from pathlib import Path
import json
r=Path(__file__).resolve().parents[1]
b=(r/'assets/CASTLE.PI1').read_bytes()
assert len(b)==32034
# Rows 112..199 are never embedded in the display asset. Source row 198,
# the first row read by REFLECT(0,199), maps to castle shoreline row 110.
pic=b[34:];rows=[min(110,y*111//199) for y in range(200)]
(r/'assets/TOP.PI1').write_bytes(b[:34]+pic[:112*160]+bytes(88*160))
(r/'assets/SOURCE.BIN').write_bytes(b''.join(pic[y*160:(y+1)*160] for y in rows))
(r/'assets/source-rows.json').write_text(json.dumps(rows)+'\n')
