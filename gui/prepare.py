"""Prepare the existing 6x6 GodLib font and a masked 16x16 pointer."""
from pathlib import Path
import struct
r=Path(__file__).resolve().parent
(r/'assets').mkdir(exist_ok=True)
(r/'assets/FONT.BIN').write_bytes((r.parent/'cutscene/assets/FONT.BIN').read_bytes())
# # is an opaque palette-0 outline; w is palette 1; . is transparent.
shape=['#...............','##..............','#w#.............','#ww#............',
 '#www#...........','#wwww#..........','#wwwww#.........','#wwwwww#........',
 '#ww#####........','#w#w#...........','##.w#...........','#..#w#..........',
 '...#w#..........','....##..........','................','................']
mask=bytearray();gfx=bytearray()
for row in shape:
 assert len(row)==16
 mask+=struct.pack('>H',sum((c=='.')<<(15-x)for x,c in enumerate(row)))
 for plane in range(4):
  gfx+=struct.pack('>H',sum((c=='w'and plane==0)<<(15-x)for x,c in enumerate(row)))
(r/'assets/CURSOR.BIN').write_bytes(mask+gfx)
