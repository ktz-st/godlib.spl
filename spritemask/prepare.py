"""Prepare a dithered 16-colour scene, independent ABC2 mask and sprite assets."""
from pathlib import Path
from PIL import Image
import hashlib,json,math,struct,subprocess,sys,tempfile
r=Path(__file__).resolve().parent
sys.path.insert(0,str(r.parent/'tools'))
from abc2_assets import convert,pack,rgb
im=Image.open(r/'assets/source.png').convert('RGB').resize((320,200),Image.Resampling.NEAREST)
pixels=list(im.get_flattened_data())
# The supplied enlarged pixel art has small RGB variations in its flat blue sky.
sky=[red<=8 and 20<=green<=38 and 95<=blue<=120 for red,green,blue in pixels]
# Repair isolated sky-coloured bark flecks before quantization. Real openings
# between branches connect to open sky, touch a screen edge, or are larger.
# Keep the small genuine fork opening at (259,30) in this supplied artwork.
seen=set();filled=[]
for start in range(320*200):
 if not sky[start] or start in seen:continue
 todo=[start];seen.add(start);component=[];edge=False
 while todo:
  i=todo.pop();component.append(i);x=i%320;y=i//320
  edge|=x==0 or x==319 or y==0 or y==199
  for nx,ny in [(x-1,y),(x+1,y),(x,y-1),(x,y+1)]:
   j=ny*320+nx
   if 0<=nx<320 and 0<=ny<200 and sky[j] and j not in seen:
    seen.add(j);todo.append(j)
 genuine_fork=30*320+259 in component
 if not edge and len(component)<=32 and not genuine_fork:
  for i in component:sky[i]=False
  filled.extend(component)
# Replace the four existing isolated stars, preserving their original locations.
star_centres=[(176,11),(231,34),(195,58),(167,130)]
for cx,cy in star_centres:
 for yy in range(cy,cy+2):
  for xx in range(cx,cx+2):
   sky[yy*320+xx]=True
# Shared palette from the approved preview, with black remapped to index 0.
palette=[(0,0,0),(0,0,34),(0,17,68),(17,34,102),(34,68,136),
         (51,102,153),(0,17,34),(0,51,102),(17,85,153),(51,136,204),
         (102,187,238),(255,255,255),(204,68,0),(255,136,0),
         (255,204,0),(255,255,51)]
words=[sum(((v//17>>1)|((v//17&1)<<3))<<shift for v,shift in zip(c,(8,4,0)))for c in palette]
levels=[1,2,3,4,5];bayer=[[0,8,2,10],[12,4,14,6],[3,11,1,9],[15,7,13,5]]
indices=[]
for y in range(200):
 t=min(1,(y/180)**1.1)*4;low=min(3,int(t));fraction=t-low
 for x in range(320):
  i=y*320+x
  if sky[i]:indices.append(levels[low+int(fraction>(bayer[y&3][x&3]+.5)/16)])
  else:indices.append(min([0,6,7,8,9,10,11],key=lambda k:sum((a-b)**2 for a,b in zip(pixels[i],palette[k]))))
scene=Image.new('P',(320,200));scene.putpalette([v for c in palette for v in c]+[0]*720);scene.putdata(indices)
scene.save(r/'assets/scene.png',bits=4)
(r/'assets/IMAGE.BIN').write_bytes(pack(indices,320,200))
(r/'assets/PALETTE.BIN').write_bytes(struct.pack('>16H',*words))
# Background indices now include nonzero colours. ABC2 therefore receives an
# independent silhouette image, never the colour scene, when producing its mask.
silhouette=Image.new('P',(320,200));silhouette.putpalette([0,0,0,255,255,255]+[0]*762)
silhouette.putdata([int(not is_sky)for is_sky in sky]);silhouette.save(r/'assets/foreground-source.png',bits=8)
abc=(r.parents[1]/'abc/abc2').resolve()
args=[str(abc),str(r/'assets/foreground-source.png'),'-atari','-mask','-bpc','4','-remap','0','0','0','-b',str(r/'assets/FORE.BIN'),'-preview',str(r/'assets/mask.png')]
p=subprocess.run(args,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT);assert p.returncode==0,p.stdout
mask=(r/'assets/FORE.BIN').read_bytes();reference=pack([int(not is_sky) for is_sky in sky],320,200,1)
assert mask==reference
(r/'assets/FORE_REF.BIN').write_bytes(reference)
assert all(indices[i] in [0,6,7,8,9,10,11] for i in filled)
meta={'converter':'curated shared palette matching approved preview; ABC2 foreground-mask export',
      'palette_words':[hex(v)for v in words],'size':[320,200],'planes':4,
      'gamut':'STE RGB444 / 4096 colours','dithering':'ordered Bayer 4x4, sky only',
      'sky_indices':levels,'gradient_in_bitmap':True,'raster_interrupts':False,
      'foreground_mask_independent_of_palette':True}

# Warm crescent: subtract an offset disc, leaving two tapered horns.
moon=[]
craters=[(-7,-6,5),(8,4,4),(-3,12,3),(8,-11,3),(-12,5,2)]
for y in range(48):
 for x in range(48):
  dx=x-23.5;dy=y-23.5;rr=dx*dx+dy*dy
  if rr>23.1**2 or (dx-9)**2+(dy+4)**2<22.5**2:moon.append(0);continue
  z=math.sqrt(max(0,1-rr/23.1**2));light=.42+.47*z-.14*dx/23.1-.08*dy/23.1
  for cx,cy,rad in craters:
   d=math.hypot(dx-cx,dy-cy)
   if d<rad:light-=.20*(1-d/rad)+.10
   elif d<rad+1:light+=.12
  moon.append(12+max(0,min(3,int(light*4))))
mi=Image.new('P',(48,48));mi.putpalette(scene.getpalette());mi.putdata(moon);mi.save(r/'assets/moon.png')
(r/'assets/MOON.BIN').write_bytes(pack(moon,48,48))
# Each phase: 48 rows, four destination words, mask + four plane words.
phases=bytearray()
for phase in range(16):
 for y in range(48):
  for group in range(4):
   values=[moon[y*48+x-phase] if 0<= (x:=group*16+j)-phase<48 else 0 for j in range(16)]
   phases+=struct.pack('>5H',sum((c!=0)<<(15-j) for j,c in enumerate(values)),*[sum(((c>>p)&1)<<(15-j) for j,c in enumerate(values))for p in range(4)])
(r/'assets/PHASES.BIN').write_bytes(phases)
# Three small four-point twinkle frames in the existing cold scene palette.
# Preserve masks have 1 outside the sprite; colour zero is transparent.
mid=min([8,9,10,11],key=lambda k:sum((a-b)**2 for a,b in zip(palette[k],(102,170,238))))
dim=min([8,9,10,11],key=lambda k:sum((a-b)**2 for a,b in zip(palette[k],(34,85,170))))
starbytes=bytearray();starframes=[]
for arm,diamond in [(1,0),(3,1),(6,3)]:
 star=[]
 for yy in range(16):
  for xx in range(16):
   dx=abs(xx-7);dy=abs(yy-7);d=dx+dy
   if dx==0 and dy<=arm or dy==0 and dx<=arm:
    star.append(11 if d<=1 else mid if d<arm else dim)
   elif d<=diamond:star.append(11 if d<=1 else mid)
   else:star.append(0)
 starframes.append(star)
 starbytes+=pack([int(c==0) for c in star],16,16,1)+pack(star,16,16)
# Mask each fixed star against the immutable scene before making GodLib sprites.
starbytes=bytearray()
for cx,cy in star_centres:
 for star in starframes:
  cut=[c if sky[(cy-7+j//16)*320+cx-7+j%16] else 0 for j,c in enumerate(star)]
  starbytes+=pack([int(c==0)for c in cut],16,16,1)+pack(cut,16,16)
(r/'assets/STARS.BIN').write_bytes(starbytes)
starpos=[(x-7,y-7,phase)for (x,y),phase in zip(star_centres,[0,43,89,137])]
(r/'assets/STARPOS.BIN').write_bytes(b''.join(struct.pack('>3H',*p)for p in starpos))
path=[(136,200)]*50+[(round(136+132*i/511),round(200-196*i/511))for i in range(768)]+[(334,-94)]*100
(r/'assets/PATH.BIN').write_bytes(b''.join(struct.pack('>hh',x,y) for x,y in path))
meta.update(source_sha256=hashlib.sha256((r/'assets/source.png').read_bytes()).hexdigest(),opaque_black_index=0,sky_pixels=sum(sky),bark_holes_filled=len(filled),bark_hole_pixels=[[i%320,i//320]for i in filled],abc2_mask_arguments=args[2:],abc2_mask_verified=True,star_count=4,star_centres=star_centres,star_cycle=192,moon_shape="crescent",moon_rgb444=["c40","f80","fc0","ff3"],moon_size=[48,48],phase_bytes=len(phases),path_frames=len(path))
(r/'assets/provenance.json').write_text(json.dumps(meta,indent=2)+'\n')
# Shareable previews show actual final palette and occlusion, not a mock-up.
frames=[]
for x,y in [path[0],path[150],path[300],path[430],path[-1]]:
 out=indices.copy()
 for sy in range(48):
  for sx in range(48):
   xx=x+sx;yy=y+sy;c=moon[sy*48+sx]
   if 0<=xx<320 and 0<=yy<200 and c and sky[yy*320+xx]:out[yy*320+xx]=c
 frame=Image.new('P',(320,200));frame.putpalette(scene.getpalette());frame.putdata(out);frames.append(frame.convert('RGB').resize((640,400),Image.Resampling.NEAREST))
strip=Image.new('RGB',(640*len(frames),400))
for i,f in enumerate(frames):strip.paste(f,(i*640,0))
strip.save(r/'analysis/preview.png')
print('Scene, ABC2 foreground mask and 16 moon phases verified.')
