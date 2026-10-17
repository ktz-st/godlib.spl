"""Independent pixel oracle: scene foreground occludes the moving lunar sprite."""
from pathlib import Path
import os,sys,subprocess,struct,json,time,hashlib,re
from PIL import Image
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
sys.path.insert(0,str(Path.home()/'.agents/skills/hatari-debugging/scripts'))
from hatari_session import HatariSession
r=Path(__file__).resolve().parents[1]
sym={p[2]:int(p[0],16)for line in subprocess.check_output(['m68k-atari-mintelf-nm',str(r/'analysis/MNDBG.PRG')],text=True).splitlines()if len(p:=line.split())==3}
def unpack(data,w,h,planes=4):
 return [sum(((int.from_bytes(data[(y*w//16+x//16)*planes*2+p*2:][:2],'big')>>(15-(x&15)))&1)<<p for p in range(planes))for y in range(h)for x in range(w)]
bg=(r/'assets/IMAGE.BIN').read_bytes();background=unpack(bg,320,200);moon=unpack((r/'assets/MOON.BIN').read_bytes(),48,48)
maskmeta=json.loads((r/'assets/provenance.json').read_text())
foreground=unpack((r/'assets/FORE_REF.BIN').read_bytes(),320,200,1)
assert (r/'assets/FORE.BIN').read_bytes()==(r/'assets/FORE_REF.BIN').read_bytes()
assert all(c in ([0,6,7,8,9,10,11] if f else [1,2,3,4,5]) for f,c in zip(foreground,background))
assert all(c!=0 for f,c in zip(foreground,background) if not f)
assert any(f and c==0 for f,c in zip(foreground,background))
assert (r/'assets/PALETTE.BIN').read_bytes()[:2]==b'\0\0'
assert maskmeta['opaque_black_index']==0
assert maskmeta['gradient_in_bitmap'] and not maskmeta['raster_interrupts']
# Source-topology regression: the continuous trunk must have no transparent grain.
assert all(foreground[y*320+x] for y in range(40,145) for x in range(286,297))
starpos=list(struct.iter_unpack('>3H',(r/'assets/STARPOS.BIN').read_bytes()))
starbytes=(r/'assets/STARS.BIN').read_bytes();stars=[unpack(starbytes[i*160+32:(i+1)*160],16,16)for i in range(12)]
path=list(struct.iter_unpack('>hh',(r/'assets/PATH.BIN').read_bytes()))
points=sorted(set([0,49,50,75,100,150,200,250,300,350,400,430,460,500,560,561,575,580,587,591,593,600,605,620,640,660,680,700,750,800,817,818,917]+[next(i for i,(x,y)in enumerate(path)if x&15==phase and y<152)for phase in range(16)]))
configs=[('st','2.06','TOS v2.06 (1991)(Atari Corp)(Mega-STE)(UK).img'),('ste','1.62','TOS v1.62 (1990)(Atari Corp)(STE)(GB)[STE TOS, Rev 2].img')]
if len(sys.argv)>1:configs=[c for c in configs if c[0]+'-'+c[1]==sys.argv[1]]
for machine,tos,rom in configs:
 tag=machine+'-'+tos
 with HatariSession(str(r/'MOON.PRG'),machine=machine,sound=False,screenshot_dir=str(r/'analysis/shots'/tag),debug_except='bus,address,illegal',extra_args=['--tos',str(Path.home()/'Atari/tos'/rom),'--memsize','1','--cpuclock','8','--cpulevel','0','--monitor','rgb','--spec512','1','--confirm-quit','false']) as h:
  h.wait(8);base=h.basepage()['text'];h.tap('P')
  def addr(name):return base+sym[name]
  def stop():h.debug('b pc = $%x :once'%addr('Screen_Update'))
  def step():h.stdin_cmd('b pc = $%x :once'%addr('Screen_Update'),settle=.02);h.stdin_cmd('c',settle=.04)
  def dump(address,size,name):
   p=r/('analysis/temp-'+tag+'-'+name+'.bin');p.unlink(missing_ok=True)
   h.stdin_cmd('savebin %s $%x $%x'%(p,address,size),settle=.03)
   for _ in range(200):
    if p.exists() and p.stat().st_size==size:break
    time.sleep(.01)
   data=p.read_bytes();assert len(data)==size;p.unlink();return data
  lo=min(v for k,v in sym.items()if k.startswith(('gMoon','gStar')));hi=max(v+4 for k,v in sym.items()if k.startswith(('gMoon','gStar')))
  def state():return dump(base+lo,hi-lo,'state')
  def word(s,k):return struct.unpack_from('>H',s,sym[k]-lo)[0]
  def lng(s,k):return struct.unpack_from('>I',s,sym[k]-lo)[0]
  stop();s=state();assert word(s,'gMoonReady')==word(s,'gMoonPaused')==1
  use_blitter=machine=='ste'
  assert word(s,'gMoonUsingBlitter')==int(use_blitter)
  # Confirm the actual function selected by Screen_Logic_DrawSprite_Clip.
  selected=struct.unpack('>I',dump(addr('gGraphicFuncsClip')+2*44+28,4,'sprite-dispatch'))[0]
  assert selected==addr('Graphic_4BP_DrawSprite_Clip_BLT' if use_blitter else 'Graphic_4BP_DrawSprite_Clip')
  phases=set();pages=set();checks=0;grass=tree=visible=0
  def check():
   global checks,grass,tree,visible
   s=state();x=struct.unpack_from('>h',s,sym['gMoonX']-lo)[0];y=struct.unpack_from('>h',s,sym['gMoonY']-lo)[0];page=lng(s,'gMoonScreen');want=bytearray(bg)
   assert 0<=x<=334 and -94<=y<=200
   tick=word(s,'gStarDrawTick')
   for starid,(px,py,offset) in enumerate(starpos):
    phase=(tick+offset)%192
    frame=0 if phase<8 else 1 if phase<16 else 2 if phase<24 else 1 if phase<32 else 0
    for j,c in enumerate(stars[starid*3+frame]):
     if not c:continue
     xx=px+j%16;yy=py+j//16;off=yy*160+(xx//16)*8;bit=1<<(15-(xx&15))
     for p in range(4):
      old=int.from_bytes(want[off+2*p:off+2*p+2],'big');v=(old&~bit)|(bit if c&(1<<p)else 0);want[off+2*p:off+2*p+2]=v.to_bytes(2,'big')
   for sy in range(48):
    for sx in range(48):
     xx=x+sx;yy=y+sy;c=moon[sy*48+sx]
     if not (0<=xx<320 and 0<=yy<200) or not c:continue
     if foreground[yy*320+xx]:
      if yy>=140:grass+=1
      if yy<110:tree+=1
      continue
     visible+=1;off=yy*160+(xx//16)*8;bit=1<<(15-(xx&15))
     for p in range(4):
      old=int.from_bytes(want[off+2*p:off+2*p+2],'big');v=(old&~bit)|(bit if c&(1<<p)else 0);want[off+2*p:off+2*p+2]=v.to_bytes(2,'big')
   actual=dump(page,32000,'screen');assert actual==want,(tag,x,y,next((i,a,b)for i,(a,b)in enumerate(zip(actual,want))if a!=b))
   assert dump(lng(s,'gMoonBackground'),32000,'background')==bg
   pages.add(page);phases.add(x&15);checks+=1;return s
  check()
  for point in points:
   h.stdin_cmd('w $%x %d %d'%(addr('gMoonStep'),point>>8,point&255),settle=.02)
   for _ in range(2):
    step();s=check();assert (struct.unpack_from('>h',s,sym['gMoonX']-lo)[0],struct.unpack_from('>h',s,sym['gMoonY']-lo)[0])==path[point]
  # Exercise every transition, expansion and shrink on both logical pages.
  for tick in [0,7,8,15,16,23,24,31,32,55,95,139,160,191]:
   h.stdin_cmd('w $%x 0 %d'%(addr('gStarTick'),tick),settle=.02)
   for _ in range(2):step();check()
  assert len(pages)==2 and len(phases)==16 and grass>0 and tree>0 and visible>0
  h.stdin_cmd('w $%x 1 174'%addr('gMoonStep'),settle=.02) # path index 430
  step();check();step();check();h.stdin_cmd('c',settle=.02);h.wait(.2);shot=h.screenshot();stop()
  s=state();raw=dump(lng(s,'gMoonScreen'),32000,'display');indices=unpack(raw,320,200)
  palwords=struct.unpack('>16H',(r/'assets/PALETTE.BIN').read_bytes())
  def rgb(v):
   if machine=='st':return tuple(((v>>shift)&7)*34 for shift in (8,4,0))
   return tuple(((((v>>shift)&7)<<1)|((v>>(shift+3))&1))*17 for shift in (8,4,0))
  expected=bytes(c for index in indices for c in rgb(palwords[index]))
  im=Image.open(shot).convert('RGB');assert im.size==(832,588)
  actual=im.crop((96,58,736,458)).resize((320,200),Image.Resampling.NEAREST).tobytes()
  assert actual==expected,(tag,'display pixel mismatch',next((i//3%320,i//960,a,b)for i,(a,b)in enumerate(zip(actual,expected))if a!=b))
  h.stdin_cmd('c',settle=.02);h.tap('SPACE');stop();s=check();assert word(s,'gMoonStep')==0
  h.stdin_cmd('c',settle=.02);h.tap('P');h.wait(.3);stop();s=check();assert word(s,'gMoonPaused')==0 and word(s,'gMoonStep')>0
  missed=lng(s,'gMoonMissedVbl');assert missed==0
  pal=struct.unpack('>16H',dump(0xffff8240,32,'palette'));expected=struct.unpack('>16H',(r/'assets/PALETTE.BIN').read_bytes());mask=0x777 if machine=='st' else 0xfff
  assert [v&mask for v in pal]==[v&mask for v in expected]
  h.stdin_cmd('c',settle=.02);h.control('hatari-event keydown 01');h.wait(.2);h.control('hatari-event keyup 01');h.wait(3)
  assert h.mem(addr('gMoonExited'),2).u16(addr('gMoonExited'))==1
  assert not any(any(e in line for e in ['Bus Error','Address Error','Illegal instruction'])for line in h.lines)
  result={'machine':machine,'tos':tos,'ram_mb':1,'cpu_mhz':8,'full_screen_checks':checks,'all_displayed_pixels_verified':True,'opaque_black_index':0,'bitmap_gradient':True,'raster_interrupts':False,'independent_foreground_mask':True,'solid_trunk_core_verified':True,'repaired_bark_pixels':maskmeta['bark_holes_filled'],'twinkling_stars':len(starpos),'star_animation_transitions_checked':True,'horizontal_phases':len(phases),'both_pages':True,'grass_occluded_pixels_checked':grass,'tree_occluded_pixels_checked':tree,'visible_moon_pixels_checked':visible,'background_unchanged':True,'godlib_sprite_renderer':'blitter' if use_blitter else 'cpu','controls_and_exit':True,'missed_vbl':missed,'screenshot':shot,'release_sha256':hashlib.sha256((r/'MOON.PRG').read_bytes()).hexdigest()}
  (r/('analysis/results-'+tag+'.json')).write_text(json.dumps(result,indent=2)+'\n');print('PASS',result,flush=True)
