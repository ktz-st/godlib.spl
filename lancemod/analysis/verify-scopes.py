"""Full-screen oracle for bars/scopes/off on all three replay engines."""
from pathlib import Path
import os,sys,struct,json,time
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
sys.path.insert(0,str(Path.home()/'.agents/skills/hatari-debugging/scripts'))
from hatari_session import HatariSession,nm_symbols
root=Path(__file__).resolve().parents[2];here=Path(__file__).resolve().parent
art=bytes(1200)+(root/'lancemod/assets/STF_VU.DAT').read_bytes()
rom=Path.home()/'Atari/tos/TOS v1.62 (1990)(Atari Corp)(STE)(De).img'
results=[]
cases=[('lancemod','LANCEMOD.TOS','LMDBG.PRG','Lance'),('leonard','LEONARD.TOS','LEODBG.PRG','Leonard'),('leonard','LEO12.TOS','LEO12DBG.PRG','Leonard'),('wizzcat','WIZZCAT.TOS','WIZDBG.PRG','Wizzcat')]
for folder,program,debug,prefix in cases:
 if len(sys.argv)>1 and sys.argv[1] not in (folder,program):continue
 r=root/folder;sy=nm_symbols(str(r/'analysis'/debug),nm='m68k-atari-mintelf-nm')
 with HatariSession(str(r/program),tos=str(rom),screenshot_dir=str(r/'analysis/shots/scopes'),debug_except='bus,address,illegal',extra_args=['--confirm-quit','false','--memsize','1','--cpuclock','8','--cpulevel','0','--monitor','rgb']) as h:
  h.wait(10);base=h.basepage()['text'];addr=lambda n:base+sy[n]
  def stop():h.debug('b pc = $%x :once'%addr(prefix+'Vis_FrameDone'),settle=.12)
  def step():
   h.stdin_cmd('b pc = $%x :once'%addr(prefix+'Vis_FrameDone'),settle=.01)
   h.stdin_cmd('c',settle=.08)
  def dump(a,n):
   p=here/'temp-scope.bin';p.unlink(missing_ok=True)
   h.stdin_cmd('savebin %s $%x $%x'%(p,a,n),settle=.02)
   for _ in range(200):
    if p.exists() and p.stat().st_size==n:break
    time.sleep(.01)
   b=p.read_bytes();assert len(b)==n;p.unlink();return b
  def u16(n):return struct.unpack('>H',dump(addr(n),2))[0]
  def u32(n):return struct.unpack('>I',dump(addr(n),4))[0]
  def v(n):return 'g'+prefix+'Vis'+n
  stop();assert u16(v('Ready'))==1
  checks=0;scope_pages=set();activity=[set() for _ in range(4)]
  def check():
   global checks
   mode,enabled,page=[u16(v(n)) for n in ('Mode','Enabled','Page')]
   ptr=u32(v('Screen'));bg=struct.unpack('>I',dump(addr('gScreenClass')+12,4))[0]
   want=bytearray(dump(bg,32000))
   if enabled and mode in (3,4):
    stereo=dump(addr(v('Stereo')),328)
    history=dump(addr(v('ScopePrevious'))+page*256,256)
    if mode==3:assert history==stereo[:256]
    else:
     mono=bytes(((int.from_bytes(stereo[i:i+1],'big',signed=True)+int.from_bytes(stereo[i+1:i+2],'big',signed=True))//2)&255 for i in range(0,256,2))
     assert history==mono+bytes(128)
    for i in range(128):
     for side,plane in enumerate([4,6] if mode==3 else [0]):
      b=stereo[i*2+side] if mode==3 else mono[i];sample=b if b<128 else b-256
      center=100 if mode==4 else [64,148][side]
      py=center-sample//4;px=32+i*2
      off=py*160+(px//16)*8+plane;mask=0xc000>>(px&15)
      w=int.from_bytes(want[off:off+2],'big')|mask
      want[off:off+2]=w.to_bytes(2,'big')
   elif enabled and mode==2:
    stereo=dump(addr(v('Stereo')),328)
    offsets=[]
    for i in range(100):
     for side,xbase in enumerate([16,176]):
      t=i*2+side
      px=xbase+((stereo[t+128]^128)>>1)
      py=68+((stereo[t]^128)>>2)
      off=py*160+(px//16)*8;mask=0x8000>>(px&15)
      w=int.from_bytes(want[off:off+2],'big')|mask
      want[off:off+2]=w.to_bytes(2,'big');offsets.append(off)
    actual_offsets=struct.unpack('>200H',dump(addr(v('XYPrevious'))+page*400,400))
    assert actual_offsets==tuple(offsets),(program,'XY saved offsets')
   elif enabled and mode==1:
    samples=dump(addr(v('Scope')),256)
    assert dump(addr(v('ScopePrevious'))+page*256,256)==samples
    scope_pages.add(ptr)
    for c,(x,y) in enumerate([(16,64),(176,64),(176,148),(16,148)]):
     trace=samples[c*64:(c+1)*64];activity[c].update(trace)
     for i,b in enumerate(trace):
      sample=b if b<128 else b-256;py=y-sample//4;px=x+i*2
      off=py*160+(px//16)*8;mask=0xc000>>(px&15)
      w=int.from_bytes(want[off:off+2],'big')|mask
      want[off:off+2]=w.to_bytes(2,'big')
   elif enabled:
    levels=struct.unpack('>4H',dump(addr(v('Level')),8))
    for c,x in enumerate([48,208,256,96]):
     for y in range(150):
      off=(36+y)*160+x//16*8
      want[off:off+8]=art[levels[c]*1200+y*8:levels[c]*1200+y*8+8]
   actual=dump(ptr,32000)
   assert actual==want,(program,mode,enabled,next((i,a,b) for i,(a,b) in enumerate(zip(actual,want)) if a!=b))
   checks+=1
  injected=set()
  # Five modes, both pages, hide/show, wraparound and synthetic amplitude extremes.
  for key,mode,enabled in [(None,0,1),('O',1,1),('O',2,1),('V',2,0),('V',2,1),('O',3,1),('V',3,0),('V',3,1),('O',4,1),('V',4,0),('V',4,1),('O',0,1),('O',1,1),('V',1,0),('V',1,1),('O',2,1),('O',3,1),('O',4,1),('O',0,1),('O',1,1)]:
   if key:
    h.stdin_cmd('c',settle=.04);h.tap(key);stop()
   assert u16(v('Mode'))==mode and u16(v('Enabled'))==enabled
   for _ in range(4):check();step()
   if enabled and mode in (3,4) and mode not in injected:
    # Pause just before the renderer reads PCM, inject extremes/crossings, then
    # prove that both the synthetic frame and later normal frames restore cleanly.
    h.stdin_cmd('b pc = $%x :once'%addr('StereoVis_DrawSplit' if mode==3 else 'StereoVis_DrawMono'),settle=.01)
    h.stdin_cmd('c',settle=.08)
    pattern=bytes([128,127,127,128,0,0,64,192]*41)
    h.stdin_cmd('w $%x '%addr(v('Stereo'))+' '.join('$%02x'%b for b in pattern),settle=.02)
    h.stdin_cmd('b pc = $%x :once'%addr(prefix+'Vis_FrameDone'),settle=.01)
    h.stdin_cmd('c',settle=.08);check()
    for _ in range(3):step();check()
    injected.add(mode)
  # Sample later music ticks too, so all channels have a chance to trigger.
  for _ in range(8):
   if all(len(s)>1 for s in activity):break
   h.stdin_cmd('c',settle=.04);h.wait(2);stop()
   for _ in range(4):check();step()
  assert len(scope_pages)==2 and all(len(s)>1 for s in activity),[len(s) for s in activity]
  for mode in (2,3,4):
   h.stdin_cmd('c',settle=.05);h.tap('O');stop()
   assert u16(v('Mode'))==mode
   for _ in range(4):check();step()
  h.stdin_cmd('c',settle=.05);shot=h.screenshot()
  h.tap('SPACE');h.wait(3)
  assert h.mem(addr(v('Exited')),2).u16(addr(v('Exited')))==1
  assert h.mem(0xffff8901,1).u8(0xffff8901)==0
  faults=[l for l in h.lines if any(e in l for e in ['Bus Error','Address Error','Illegal instruction'])]
  (r/('analysis/scopes-'+program+'.log')).write_text('\n'.join(h.lines))
  assert not faults,faults
  record=dict(program=program,tos='1.62-de',machine='STE',mhz=8,ram_mb=1,full_screen_checks=checks,both_scope_pages=True,ice_xy=True,stereo_split_mono=True,synthetic_extremes=True,channel_distinct_samples=[len(s) for s in activity],switch_hide_show=True,clean_exit=True,screenshot=shot)
  results.append(record);print(program,'PASS',checks,'full pages',flush=True)
  (here/'stereo-results.json').write_text(json.dumps(results,indent=2)+'\n')
