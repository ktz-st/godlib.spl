#!/usr/bin/env python3
from pathlib import Path
from PIL import Image
import math,struct,hashlib,json
APP=Path(__file__).resolve().parents[1];ROOT=APP.parents[1];OUT=APP/'assets';SRC=APP/'source'
def rgb(word):return tuple(((((word>>s)&7)<<1)|((word>>(s+3))&1))*17 for s in (8,4,0))
def pack(idx):
 out=bytearray()
 for y in range(160):
  for w in range(20):
   for p in range(4):out.extend(struct.pack('>H',sum(((idx[y*320+w*16+bit]>>p)&1)<<(15-bit)for bit in range(16))))
 return out
pictures=[]
for i in range(2):
 png=SRC/f'SCENE{i}.png';pal=SRC/f'PALETTE{i}.BIN';suffix='2'if i else''
 if not png.exists():
  original=ROOT/'godlib.spl/crt/assets';words=struct.unpack('>16H',(original/f'PALETTE{suffix}.BIN').read_bytes());idx=(original/f'INDICES{suffix}.BIN').read_bytes()[24*320:184*320]
  image=Image.frombytes('P',(320,160),idx);colours=[v for word in words[:8]for v in rgb(word)];image.putpalette(colours+[0]*(768-len(colours)));image.save(png,bits=4)
  pal.write_bytes(struct.pack('>16H',*(list(words[:8])+[0]*7+[0xfff])))
 im=Image.open(png);assert im.mode=='P'and im.size==(320,160);idx=im.tobytes();assert max(idx)<8
 native=pack(idx);(OUT/f'IMAGE{i}.BIN').write_bytes(native);(OUT/f'PALETTE{i}.BIN').write_bytes(pal.read_bytes())
 palwords=struct.unpack('>16H',pal.read_bytes())
 stages=b''.join(struct.pack('>16H',*[palwords[j] if j<n or j==15 else 0 for j in range(16)]) for n in range(9))
 (OUT/f'STAGES{i}.BIN').write_bytes(stages)
 pictures.append({'source':png.name,'source_sha256':hashlib.sha256(png.read_bytes()).hexdigest(),'native_bytes':len(native),'native_sha256':hashlib.sha256(native).hexdigest(),'palette_words':[hex(v)for v in struct.unpack('>16H',pal.read_bytes())],'origin':f'CRT ABC2 8-colour scene {i+1}, source frame crop Y=24..183 (artwork Y=8..167)'})
# Retain the original inward angular/radius traversal, quantized to 8x8 cells.
order=[];seen=set()
for angle in range(18801):
 r=188-angle*.01;a=math.radians(90+angle);x=int(159+r*math.cos(a));y=int(100+r*math.sin(a))
 if not(0<=x<320 and 0<=y<200):continue
 tile=(x//8,(y*4//5)//8)
 if tile not in seen:seen.add(tile);order.append(tile)
missing=[(x,y)for y in range(20)for x in range(40)if(x,y)not in seen]
missing.sort(key=lambda xy:-((xy[0]*8+4-160)**2+((xy[1]*8+4-80)*1.25)**2));order+=missing
assert len(order)==800 and len(set(order))==800
snake=[(x,y)for y in range(16)for x in (range(20)if not y&1 else range(19,-1,-1))]
spiral_offsets=[y*8*160+(x//2)*8+(x&1)for x,y in order];snake_offsets=[y*10*160+x*8 for x,y in snake]
height=[0]+[max(1,16-max(n-2,0)//10)for n in range(1,161)]
first=[(n+2*height[n]+14)*160 for n in range(161)]
lines=['; Small geometry tables, not rendered frames.','Lw_SpiralOffsets:']
for name,values in [('spiral',spiral_offsets),('Lw_SnakeOffsets',snake_offsets),('Lw_RowOffsets',[i*160 for i in range(160)]),('Lw_FoldFirst',first)]:
 if name!='spiral':lines.append(name+':')
 for start in range(0,len(values),16):lines.append('        dc.w '+','.join(map(str,values[start:start+16])))
lines+=['Lw_FoldHeight:']
for start in range(0,len(height),16):lines.append('        dc.b '+','.join(map(str,height[start:start+16])))
lines+=['        even']
centre_open=[y for i in range(80) for y in (79-i,80+i)]
centre_close=[y for i in range(80) for y in (i,159-i)]
inter_rows=[y for i in range(0,160,2) for y in (i,159-i)]
curtain_cols=[x for i in range(160) for x in (i,319-i)]
inter_cols=[x for i in range(0,320,2) for x in (i,319-i)]
for name,values in [('Lw_CentreOpen',[y*160 for y in centre_open]),('Lw_CentreClose',[y*160 for y in centre_close]),('Lw_InterRowOffsets',[y*160 for y in inter_rows]),('Lw_CurtainColumns',[v for x in curtain_cols for v in ((x//16)*8,0x8000>>(x&15))]),('Lw_InterColumns',[v for x in inter_cols for v in ((x//16)*8,0x8000>>(x&15))])]:
 lines.append(name+':')
 for start in range(0,len(values),16):lines.append('        dc.w '+','.join(map(str,values[start:start+16])))
limits=[800,160,20,320,1,8,160,160,160,320,320];speeds=[16,2,1,4,1,1,2,2,2,2,2]
assert sorted(centre_open)==sorted(centre_close)==sorted(inter_rows)==list(range(160))
assert sorted(curtain_cols)==sorted(inter_cols)==list(range(320))
lines+=['        even'];(OUT/'tables.inc').write_text('\n'.join(lines)+'\n')
(OUT/'geometry.json').write_text(json.dumps({'spiral':order,'spiral_fallback_cells':len(missing),'snake':snake,'fold_height':height,'fold_source_first_unclipped':[(n+2*height[n]+14)for n in range(161)],'centre_open':centre_open,'centre_close':centre_close,'inter_rows':inter_rows,'curtain_cols':curtain_cols,'inter_cols':inter_cols,'limits':limits,'speeds':speeds,'palette_vbl_delay':5},indent=2)+'\n')
(OUT/'source.json').write_text(json.dumps({'pictures':pictures,'image_viewport':[0,24,320,160],'hud_palette_index':15,'original_code':'All 7 appear + 7 disappear entries of LCK4/LCK5; full mapping in README.md and DCK/EFFECTS-AUDIT.md','adaptations':['320x160 stage with persistent HUD','spiral quantized to unique 8x8 cells; duplicate visits removed, missed cells appended','fold height shrinks once per 10 rows instead of 13 for 200-line original; source row = n+2*h+14-j, clamped to 159','four snake blocks per update; opening counterparts and reversible fold added','independent progress/row history on both display pages; palette switches on black','all 14 original entries represented by 11 paired modes; added opposite directions where absent','centre/curtain bounds symmetrized to 0..159 and 0..319; no original out-of-screen writes','colour steps use 8 scene colours at 5 VBL each; HUD index 15 remains white','smear repeats source row 160-progress above the revealed tail, with a reverse closing counterpart']},indent=2)+'\n')
print('Prepared 2 x 25600-byte images, 800 spiral cells, 320 snake blocks;',len(missing),'spiral fallback cells.')
