"""Independent pixel reference, original glyph stream, both display pages and waves."""
from pathlib import Path
import json,os,re,struct,subprocess,sys,time
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
sys.path.insert(0,str(Path.home()/'.agents/skills/hatari-debugging/scripts'))
from hatari_session import HatariSession
root=Path(__file__).resolve().parents[1]
sym={p[2]:int(p[0],16) for l in subprocess.check_output(['m68k-atari-mintelf-nm',str(root/'analysis/NDBG.PRG')],text=True).splitlines() if len(p:=l.split())==3}
font=(root/'assets/LOST16.FON').read_bytes()
message=''.join(re.findall(r"dc.b '([^']*)'",(root/'nibble_s.s').read_text())).encode()
waves=[struct.unpack('>320h',(root/'assets'/p).read_bytes()) for p in ['NIBBLE.DAT','NIBBLE1.DAT']]
waves.append((3200,)*320)  # Flat text begins at Y=81+20.
configs=[('st','2.06','TOS v2.06 (1991)(Atari Corp)(Mega-STE)(UK).img'),('ste','2.06','TOS v2.06 (1991)(Atari Corp)(Mega-STE)(UK).img'),('ste','1.62','TOS v1.62 (1990)(Atari Corp)(STE)(GB)[STE TOS, Rev 2].img')]
if len(sys.argv)>1:configs=[c for c in configs if c[0]+'-'+c[1]==sys.argv[1]]
results=[]
for machine,version,rom in configs:
 label=machine+'-'+version
 with HatariSession(str(root/'NIBBLE.PRG'),machine=machine,sound=False,screenshot_dir=str(root/'analysis/shots'/label/str(int(time.time()))),debug_except='bus,address,illegal',extra_args=['--tos',str(Path.home()/'Atari/tos'/rom),'--confirm-quit','false','--memsize','1','--cpulevel','0','--cpuclock','8','--monitor','rgb']) as h:
  h.wait(8);base=h.basepage()['text'];shot=h.screenshot()
  def addr(n):return base+sym[n]
  def stop():h.debug('b pc = $%x :once'%addr('Screen_Update'))
  def dump(a,size,name):
   p=root/('analysis/temp-'+label+'-'+name+'.bin')
   p.unlink(missing_ok=True)
   h.stdin_cmd('savebin %s $%x $%x'%(p,a,size),settle=.04)
   for i in range(200):
    if p.exists() and p.stat().st_size==size:break
    time.sleep(.01)
   data=p.read_bytes();assert len(data)==size,(name,len(data),size);p.unlink();return data
  def write(n,data):h.stdin_cmd('w $%x '%addr(n)+' '.join('$%02x'%v for v in data),settle=.03)
  first=min(v for k,v in sym.items() if k.startswith('gNibble'));last=sym['gScreenClass']+42
  def state():return dump(base+first,last-first,'state')
  def word(s,n):return struct.unpack_from('>H',s,sym[n]-first)[0]
  def lng(s,n):return struct.unpack_from('>I',s,sym[n]-first)[0]
  stop();s=state();assert word(s,'gNibbleReady')==1
  bgptr=struct.unpack_from('>I',s,sym['gScreenClass']+12-first)[0];background=dump(bgptr,32000,'background')
  pages=set();phases=[set(),set(),set()];checks=0
  def check():
   global checks
   s=state();phase=word(s,'gNibbleFramePhase');wave=word(s,'gNibbleFrameWave');phases[wave].add(phase)
   buf=s[sym['gNibbleBuffer']-first:sym['gNibbleBuffer']-first+600]
   current=lng(s,'gNibbleText')-addr('Nibble_Text')-1
   progress=(17-word(s,'gNibbleCount'))*2
   assert 0<=current<len(message) and 2<=progress<=32,(current,progress)
   expected_buffer=bytearray(600);target=bytearray(background)
   # Model a 320-pixel horizontal text stream, independent of the ROXL chain.
   for x in range(320):
    relative=x-(320-progress);ch=message[(current+relative//32)%len(message)];gx=relative%32
    for y in range(15):
     if font[(ch-32)*64+y*4+gx//8]&(128>>(gx&7)):
      expected_buffer[(x//16)*30+y*2+(x&15)//8]|=128>>(x&7)
      dy=81+waves[wave][phase*2+x//8]//160+y
      target[dy*160+(x//16)*8+(x&15)//8]|=128>>(x&7)
   assert buf==expected_buffer,(label,'glyph conveyor',current,progress)
   page=lng(s,'gNibbleScreen');pages.add(page);actual=dump(page,32000,'screen')
   if actual!=target:
    (root/('analysis/failure-'+label+'.bin')).write_bytes(actual)
    raise AssertionError((label,'pixels',wave,phase,next((i,a,b) for i,(a,b) in enumerate(zip(actual,target)) if a!=b)))
   checks+=1
   return s
  check()
  # Natural consecutive frames preserve the original sparse-erasure contract.
  for wave in range(3):
   if wave:
    h.stdin_cmd('c',settle=.04);h.tap(str(wave+1));stop()
   for frame in range(82):
    check()
    if frame%20==0:print(label,'wave',wave+1,'verified',frame+1,'frames',flush=True)
    h.stdin_cmd('b pc = $%x :once'%addr('Screen_Update'),settle=.02)
    h.stdin_cmd('c',settle=.04)
   assert phases[wave]==set(range(80)),(label,wave,sorted(phases[wave]))
  # Pause and switch both ways: the per-page clear must remove old-wave pixels.
  h.stdin_cmd('c',settle=.04);h.tap('SPACE');stop();assert word(state(),'gNibblePaused')==1
  for key,wave in [('1',0),('3',2),('2',1),('3',2),('1',0)]:
   h.stdin_cmd('c',settle=.04);h.tap(key);stop();s=check();assert word(s,'gNibbleFrameWave')==wave
   p=word(s,'gNibblePhase');h.stdin_cmd('c',settle=.04);h.wait(.15);stop();s=check();assert word(s,'gNibblePhase')==p
  h.stdin_cmd('c',settle=.04);h.tap('R');stop();assert word(state(),'gNibbleRaster')==1
  # Force a pending final character, then let >320 pixels flush the old history.
  write('gNibbleText',struct.pack('>I',addr('Nibble_Text')+len(message)-1));write('gNibbleCount',struct.pack('>H',1))
  h.stdin_cmd('c',settle=.04);h.tap('SPACE');h.wait(4);h.tap('SPACE');stop();s=check()
  assert lng(s,'gNibbleText')<addr('Nibble_Text')+30,'text did not wrap'
  assert word(s,'gNibblePaused')==1 and len(pages)==2
  missed=lng(s,'gNibbleMissedVbl');assert missed==0,(label,missed)
  h.stdin_cmd('c',settle=.04)
  h.control('hatari-event keydown 01');h.wait(.3);h.control('hatari-event keyup 01');h.wait(4)
  assert h.mem(addr('gNibbleExited'),2).u16(addr('gNibbleExited'))==1
  faults=[l for l in h.lines if any(e in l for e in ('Bus Error','Address Error','Illegal instruction'))];assert not faults,faults
  result={'machine':machine,'tos':version,'cpu_mhz':8,'ram_mb':1,'checks_full_32000_bytes':checks,'wave_phases_verified':[sorted(p) for p in phases],'both_pages':True,'glyph_stream_and_wrap':True,'pause_wave_switch_raster_exit':True,'missed_vbl':missed,'screenshot':shot}
  results.append(result);(root/('analysis/verification-'+label+'.log')).write_text('\n'.join(h.lines));print(label,'PASS',checks,'complete screens',flush=True)
(root/('analysis/results'+('-'+sys.argv[1] if len(sys.argv)>1 else '')+'.json')).write_text(json.dumps(results,indent=2)+'\n')
