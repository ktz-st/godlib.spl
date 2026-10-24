"""Original DCK atlas/TRJ, packed for MOVEP/MOVEM. No generated frame cache."""
from pathlib import Path
import struct,json,hashlib
from PIL import Image
r=Path(__file__).resolve().parents[1];im=Image.open(r/'source/BIG.png');pi=(r/'source/BIG.PI1').read_bytes();trj=(r/'source/SCROLL_1.TRJ').read_bytes()
columns=bytearray();rows=bytearray()
for g in range(49):
 def pixel(x,y):return im.getpixel((g%8*40+x,g//8*32+y)) if g<48 else 0
 for c in range(5):
  for y in range(32):
   columns.extend(sum(((pixel(c*8+x,y)>>p)&1)<<(7-x) for x in range(8)) for p in range(4))
 for y in range(32):
  for group in range(3):
   size=16 if group<2 else 8
   for p in range(4):rows.extend(sum(((pixel(group*16+x,y)>>p)&1)<<(size-1-x)for x in range(size)).to_bytes(size//8,'big'))
(r/'assets/COLUMNS.BIN').write_bytes(columns);(r/'assets/ROWS.BIN').write_bytes(rows);(r/'assets/PALETTE.BIN').write_bytes(pi[2:34])
raw=[list(struct.unpack_from('>40h',trj,i*80))for i in range(10)];paths=[]
for path in raw:
 lo,hi=min(path),max(path);scale=min(1,120/max(1,hi-lo));paths.append([round(84+(y-(lo+hi)/2)*scale)for y in path])
(r/'assets/PATHS.BIN').write_bytes(b''.join(struct.pack('>h',y)for path in paths for y in path))
cells={c:i for i,c in enumerate('ABCDEFGHIJKLMNOPQRSTUVWXYZ')};cells.update({'!':26,"'":27,'(':28,')':29,'-':30,'.':31,'?':32,':':33,',':44});cells.update({str(i):34+i for i in range(10)})
# DCK commands are consumed by the entering-glyph decoder (nine-glyph lookahead).
segments=[('P2','GODLIB AND DCK - ONE TEXT, MANY ROUTES!   '),('P7','FOLLOW THE WAVE - NO FRAME CACHE!   '),('P4','STAIRS IN FULL COLOUR!   '),('H','A STRAIGHT HORIZONTAL STRIP!   '),('V','VERTICAL!   '),('P0','BACK TO THE CURVES!   '),('P9','UP AND DOWN - THE STORY CONTINUES!   ')]
encoded=[]
for commands,text in segments:
 for c in commands:encoded.extend([254,ord(c)])
 encoded.extend(cells.get(c,48)for c in text)
encoded.append(255)
(r/'assets/text.inc').write_text('Route_Text:\n        dc.b '+','.join(map(str,encoded))+'\n        even\nRoute_ColumnGlyphs:\n'+''.join('        dc.l Route_Columns+%d\n'%(i*640)for i in range(49))+'Route_RowGlyphs:\n'+''.join('        dc.l Route_Rows+%d\n'%(i*640)for i in range(49)))
(r/'assets/source.json').write_text(json.dumps({'font':'DCK disk B FONTES/BIG.PC1, lossless PI1','font_sha256':hashlib.sha256(pi).hexdigest(),'trj':'DCK disk B TRAJ_SCR.OLL/SCROLL_1.TRJ','trj_sha256':hashlib.sha256(trj).hexdigest(),'raw_paths':raw,'paths':paths,'adaptation':'Original path shapes centred at Y84; only profiles taller than 120 rows scaled down. P/H curves morph 1px/update. Fixed H Y84; fixed V X144,Y24,height160. Nine-glyph queue shared across all modes.','glyph':[40,32],'vertical_pitch':40,'segments':segments,'text_bytes':encoded},indent=2)+'\n')
