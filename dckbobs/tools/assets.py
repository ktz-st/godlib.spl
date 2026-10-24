#!/usr/bin/env python3
from pathlib import Path
import hashlib,json,struct,shutil
app=Path(__file__).resolve().parents[1];root=app.parents[1];src=app/'source';out=app/'assets'
source=root/'DCK/extracted';pic=src/'BALLS.PI1'
if not pic.exists():shutil.copyfile(source/'pi1/sprite/BALLS.PI1',pic)
names=['NOEUD','CERCLE','2CERCLES','DOUBLE45','CER-45','CER_45~1','GROS_CER','REBOND']
for n in names:
 p=src/'paths'/f'{n}.DAT'
 if not p.exists():shutil.copyfile(source/'disk-b/TRAJ_SPR.ITE'/p.name,p)
b=pic.read_bytes();assert len(b)==32034;raw=b[34:];blob=bytearray();meta=[]
for n in range(3):
 gfx=bytearray();mask=bytearray()
 for y in range(n*27,n*27+27):
  for w in range(2):
   words=struct.unpack_from('>4H',raw,y*160+w*8);gfx.extend(struct.pack('>4H',*words));m=~(words[0]|words[1]|words[2]|words[3])&0xffff;mask.extend(struct.pack('>H',m))
 assert len(gfx)==432 and len(mask)==108;blob.extend(gfx+mask)
 meta.append({'colour':['red','blue','green'][n],'source_rect':[0,n*27,32,27],'gfx_bytes':len(gfx),'mask_bytes':len(mask)})
(out/'SPRITES.BIN').write_bytes(blob);(out/'PALETTE.BIN').write_bytes(b[2:34])
paths=bytearray();records=[];inc=[];lengths=[]
for i,n in enumerate(names):
 p=src/'paths'/f'{n}.DAT';original=p.read_bytes();xy=list(struct.iter_unpack('>hh',original));offset=len(paths)
 # Same point order and cadence, fitted offline into the 320x200 example's stage.
 mapped=[(x*24//25,32+y*3//5)for x,y in xy]
 assert all(0<=x<=288 and 32<=y<=140 for x,y in mapped)
 for x,y in mapped:paths.extend(struct.pack('>hh',x,y))
 inc.append(f'        dc.l Bobs_PathData+{offset}');lengths.append(len(xy))
 records.append({'name':n,'points':len(xy),'offset':offset,'source_sha256':hashlib.sha256(original).hexdigest(),'source_bounds':[min(x for x,y in xy),min(y for x,y in xy),max(x for x,y in xy),max(y for x,y in xy)]})
(out/'PATHS.BIN').write_bytes(paths);(out/'paths.inc').write_text('Bobs_Paths:\n'+'\n'.join(inc)+'\nBobs_Lengths:\n        dc.w '+','.join(str(n)for n in lengths)+'\n')
report={'source':'DCK disk B / SPRITE/BALLS.PC1, TRAJ_SPR.ITE/*.DAT','picture_sha256':hashlib.sha256(b).hexdigest(),'sprites':meta,'paths':records,'coordinate_transform':'x=floor(rawX*24/25); y=32+floor(rawY*3/5); source point order/cadence retained','phase_separation_points':12,'palette':'original 16 ST RGB333 entries; index 0 transparent','embedded_bytes':len(paths)+len(blob)+32}
(out/'source.json').write_text(json.dumps(report,indent=2)+'\n');print('Prepared',len(paths),'path bytes and',len(blob),'sprite bytes.')
