#!/usr/bin/env python3
"""Build identical loose, raw-LNK and whole-GodPack-LNK assets."""
from pathlib import Path
import sys,struct,re,json,hashlib,subprocess
root=Path(__file__).resolve().parent;god=root.parents[1]/'godlib'
sys.path.insert(0,str(god/'tools/toolbase'));import toolbase as t
loose=root/'UNLINK/SCENE';loose.mkdir(parents=True,exist_ok=True);(root/'DATA').mkdir(exist_ok=True)
# Reuse our ABC2 STE castle; preserve its indexed palette and exact planar pixels.
source=root.parent/'reflect/assets/CASTLE.PI1'
(loose/'CASTLE.PI1').write_bytes(source.read_bytes()[:32034])
raw=bytes(int(v,16)for v in re.findall(r'0x([0-9A-Fa-f]{2})',(god/'font8x8/fontdata.c').read_text()))
frames=[]
for c in range(32,127):
 pixels=[0]*128;mask=[True]*128
 for y in range(8):
  for x in range(8):
   if raw[(c-32)*8+y]&(0x80>>x):pixels[y*16+x]=14;mask[y*16+x]=False
 frames.append(t.planar_sprite(16,8,4,4,pixels,mask))
data=bytearray(t.serialize_bfb(frames,t.SpriteDef(font=True,charfirst=32,charlast=126,spacewidth=8)));data[10]=0
offset=struct.unpack_from('>I',data,28)[0]
for i in range(95):struct.pack_into('>4H',data,offset+i*8,0,0,7,7)
struct.pack_into('>2H',data,12,8,8);(loose/'FONT.BFB').write_bytes(data)
# Eight masked crystal/spark frames, derived directly as indexed sprite pixels.
frames=[]
for phase in range(8):
 pixels=[0]*384;mask=[True]*384;r=4+[0,1,2,3,4,3,2,1][phase]
 for y in range(24):
  for x in range(16):
   dx=x-7;dy=y-11;d=abs(dx)*2+abs(dy)
   if d<=r*2:
    pixels[y*16+x]=14 if d<r else (6 if dx+dy<0 else 13);mask[y*16+x]=False
 frames.append(t.planar_sprite(16,24,4,4,pixels,mask))
(loose/'SPARKS.BSB').write_bytes(t.serialize_bsb(frames))
t.makelink(loose,root/'DATA/SCENE.LNK')
subprocess.run([str(t.find_godpack_tool()),str(root/'DATA/SCENE.LNK'),str(root/'DATA/PACKED.LNK')],check=True)
report={'source':'reflect/assets/CASTLE.PI1, ABC2 STE; GodLib 8x8 font; generated masked spark frames',
 'assets':{p.name:{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}for p in sorted(loose.iterdir())if p.is_file()},
 'raw_link_bytes':(root/'DATA/SCENE.LNK').stat().st_size,'packed_link_bytes':(root/'DATA/PACKED.LNK').stat().st_size}
(root/'assets/build.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
