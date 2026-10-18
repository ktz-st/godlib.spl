"""ABC2 STE 8 colours, no dithering; bright/dark banks and guarded blit sources."""
from pathlib import Path
from PIL import Image,ImageOps
import sys,struct,json,hashlib
root=Path(__file__).resolve().parent
sys.path.insert(0,str(root.parent/'tools'))
from abc2_assets import convert,pack
def prepare(number):
 suffix='' if number==1 else str(number)
 source=root/('assets/postapoc'+suffix+'-source.png')
 im=ImageOps.fit(Image.open(source).convert('RGB'),(320,176),method=Image.Resampling.LANCZOS)
 words,idx,preview,meta=convert(im,planes=3,locks={0:0,7:0xfff})
 full=[0]*64000
 for y in range(176):full[(y+16)*320:(y+17)*320]=idx[y*320:(y+1)*320]
 base=full.copy()
 for y in range(17,192,2):
  for x in range(320):base[y*320+x]|=8
 (root/('assets/IMAGE'+suffix+'.BIN')).write_bytes(pack(base,320,200,4))
 (root/('assets/INDICES'+suffix+'.BIN')).write_bytes(bytes(full))
 planes=bytearray()
 for p in range(3):
  for y in range(-2,202):
   for w in range(-1,21):
    bits=0
    if 0<=y<200 and 0<=w<20:
     bits=sum(((full[y*320+w*16+j]>>p)&1)<<(15-j)for j in range(16))
    planes+=struct.pack('>H',bits)
 (root/('assets/SOURCE'+suffix+'.BIN')).write_bytes(planes)
 def enc(n):return (n>>1)|((n&1)<<3)
 dark=[]
 for word in words:
  rgb=[(((word>>s)&7)<<1)|((word>>(s+3))&1)for s in [8,4,0]]
  dark.append(sum(enc(n//2)<<s for n,s in zip(rgb,[8,4,0])))
 (root/('assets/PALETTE'+suffix+'.BIN')).write_bytes(struct.pack('>16H',*(words+dark)))
 preview.save(root/('assets/postapoc'+suffix+'-8col.png'))
 meta.update({'source':source.name,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'artwork_viewport':[0,16,320,176],'palette_locks':{'0':'black','7':'white'},'dark_bank_scale':'floor(channel / 2)','source_planes':[3,204,22],'source_bytes':len(planes),'reference':'superhex_ste/src/main.c:891 rbt_band; CRT adapted to three image planes plus independent dim mask'})
 (root/('assets/provenance'+suffix+'.json')).write_text(json.dumps(meta,indent=2)+'\n')
 print('ABC2:',source.name,'8 STE colours; guarded source',len(planes),'bytes')
for number in (1,2):prepare(number)
# Opening is the exact reverse of off: a dim short line, bright thin line,
# then an increasingly tall image whose palette returns from overbright.
# No round dot. The core is 2 pixels high with a subtle 4-pixel halo.
lights=[(40,2,1),(40,2,4),(40,2,8),(40,2,12),
        (64,4,15),(96,4,15),(144,4,15),(208,4,15),(264,4,15),(320,4,15)]
heights=[2,6,12,22,36,54,78,106,138,168,200]
shapes=[(0,0)]+[(w,h)for w,h,b in lights]+[(320,h)for h in heights]
image_start=1+len(lights)
lines=['; Offline row maps and RGB444 palettes; no runtime scaling division.',
       '        section data','        even',
       '        xdef Crt_TvSteps,Crt_TvCount,Crt_TvPalettes,Crt_TvPalettes2',
       'Crt_TvCount: dc.w '+str(len(shapes)), 'Crt_TvSteps:']
for i,(w,h)in enumerate(shapes):
 lines+=['        dc.w %d,%d'%(w,h),'        dc.l Crt_TvRows%d'%i if i>=image_start else '        dc.l 0']
for i,(w,h)in enumerate(shapes):
 if i<image_start:continue
 rows=[(100+(int((y-h//2)*200/h)))*160 for y in range(h)]
 assert all(0<=n<32000 for n in rows)
 lines+=['Crt_TvRows%d: dc.w '%i+','.join(map(str,rows))]
def enc(n):return (n>>1)|((n&1)<<3)
def colour(rgb):return sum(enc(n)<<s for n,s in zip(rgb,[8,4,0]))
palette_reference=[]
for suffix in ('','2'):
 original=struct.unpack('>16H',(root/('assets/PALETTE'+suffix+'.BIN')).read_bytes())
 lines+=['Crt_TvPalettes'+suffix+':']
 stages=[]
 for i,(w,h)in enumerate(shapes):
  if i==0:pal=[0]*16
  elif i<image_start:
   intensity=lights[i-1][2];pal=[0]*16
   pal[1]=colour([intensity//3]*3) # faint outer glow
   pal[7]=colour([intensity]*3)    # thin bright core fading to black
  else:
   # Original NIEZW boosts RGB channels independently, keeping black black.
   boost=(200-h)*12//198
   pal=[]
   for word in original:
    if word==0:pal.append(0);continue
    rgb=[(((word>>shift)&7)<<1)|((word>>(shift+3))&1)for shift in [8,4,0]]
    pal.append(colour([min(15,n+boost)for n in rgb]))
  assert pal[0]==0 and pal[8]==0
  stages.append(pal)
  lines+=['        dc.w '+','.join('$%03x'%word for word in pal)]
 palette_reference.append(stages)
(root/'assets/TVSTEPS.S').write_text('\n'.join(lines)+'\n')
(root/'assets/tvsteps.json').write_text(json.dumps(shapes)+'\n')
(root/'assets/tvpalettes.json').write_text(json.dumps({'image_start':image_start,'palettes':palette_reference})+'\n')
