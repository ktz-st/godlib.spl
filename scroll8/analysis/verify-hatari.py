"""Independent pixel stream: all eight font rows, cache wraps and both pages."""
from pathlib import Path
import json,os,re,struct,subprocess,sys,time
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
sys.path.insert(0,str(Path.home()/'.agents/skills/hatari-debugging/scripts'))
from hatari_session import HatariSession
root=Path(__file__).resolve().parents[1]
sym={p[2]:int(p[0],16) for l in subprocess.check_output(['m68k-atari-mintelf-nm',str(root/'analysis/S8DBG.PRG')],text=True).splitlines() if len(p:=l.split())==3}
font=bytes(int(v,16) for v in re.findall(r'0x([0-9A-Fa-f]{2})',(root.parent.parent/'godlib/font8x8/fontdata.c').read_text()))
message=json.loads(re.search(r'const char gTinyText\[\] = ("[^\n]*?") ',(root/'text.h').read_text())[1]).encode()
assert len(message)%2==0
configs=[('st','2.06','TOS v2.06 (1991)(Atari Corp)(Mega-STE)(UK).img'),('ste','2.06','TOS v2.06 (1991)(Atari Corp)(Mega-STE)(UK).img'),('ste','1.62','TOS v1.62 (1990)(Atari Corp)(STE)(GB)[STE TOS, Rev 2].img')]
if len(sys.argv)>1:configs=[c for c in configs if c[0]+'-'+c[1]==sys.argv[1]]
results=[]
for machine,version,rom in configs:
 tag=machine+'-'+version
 with HatariSession(str(root/'SCROLL8.PRG'),machine=machine,sound=False,screenshot_dir=str(root/'analysis/shots'/tag/str(int(time.time()))),debug_except='bus,address,illegal',extra_args=['--tos',str(Path.home()/'Atari/tos'/rom),'--confirm-quit','false','--memsize','1','--cpuclock','8','--cpulevel','0','--monitor','rgb']) as h:
  h.wait(8);base=h.basepage()['text'];shot=h.screenshot()
  def addr(n):return base+sym[n]
  def stop():h.debug('b pc = $%x :once'%addr('Screen_Update'))
  def dump(a,size,name='dump'):
   p=root/('analysis/temp-'+tag+'-'+name+'.bin');p.unlink(missing_ok=True)
   h.stdin_cmd('savebin %s $%x $%x'%(p,a,size),settle=.04)
   for i in range(200):
    if p.exists() and p.stat().st_size==size:break
    time.sleep(.01)
   b=p.read_bytes();assert len(b)==size;p.unlink();return b
  first=min(v for k,v in sym.items() if k.startswith('gTiny'))
  last=max(sym['gTinyGStorage']+5384,sym['gScreenClass']+42,max(v+4 for k,v in sym.items() if k.startswith('gTiny')))
  def state():return dump(base+first,last-first,'state')
  def word(s,n):return struct.unpack_from('>H',s,sym[n]-first)[0]
  def lng(s,n):return struct.unpack_from('>I',s,sym[n]-first)[0]
  def step():
   h.stdin_cmd('b pc = $%x :once'%addr('Screen_Update'),settle=.02);h.stdin_cmd('c',settle=.04)
  stop();s=state();assert word(s,'gTinyReady')==1
  assert dump(addr('gFont8x8'),len(font),'font')==font
  mcpos=set();gpos=set();mcphase=set();gphase=set();pages=set();checks=0
  def check():
   global checks
   s=state();mode=word(s,'gTinyFrameMode');m=lng(s,'gTinyFrameMC');g=lng(s,'gTinyFrameG')
   bgptr=struct.unpack_from('>I',s,sym['gScreenClass']+12-first)[0]
   want=bytearray(dump(bgptr,32000,'background'))
   for enabled,y,start in [(mode&1,88,2*m-322),(mode&2,120,2*g-320)]:
    if not enabled:continue
    for x in range(320):
     ch=message[((start+x)//8)%len(message)];gx=(start+x)&7
     for row in range(8):
      if font[(ch-32)*8+row]&(128>>gx):want[(y+row)*160+(x//16)*8+(x&15)//8]|=128>>(x&7)
   if mode==3:assert (2*m-322)%(len(message)*8)==(2*g-320)%(len(message)*8),(m,g)
   page=lng(s,'gTinyScreen');pages.add(page);actual=dump(page,32000,'screen')
   if actual!=want:
    (root/('analysis/failure-'+tag+'.bin')).write_bytes(actual)
    raise AssertionError((tag,'pixels',mode,m,g,next((i,a,b) for i,(a,b) in enumerate(zip(actual,want)) if a!=b)))
   mcpos.add(word(s,'gTinyMCPos'));gpos.add(word(s,'gTinyGPos'));mcphase.add(word(s,'gTinyMCPhase'));gphase.add(word(s,'gTinyGPhase'))
   checks+=1;return s
  for i in range(260):
   check();step()
   if i%64==63:print(tag,'PASS synchronized screens',i+1,flush=True)
  assert mcpos==set(range(40)) and gpos==set(range(0,42,2))
  assert mcphase=={0,2,4,6} and gphase==set(range(0,16,2)) and len(pages)==2
  h.stdin_cmd('c',settle=.04);h.tap('SPACE');stop();s=check();assert word(s,'gTinyPaused')==1
  frozen=(lng(s,'gTinyFrameMC'),lng(s,'gTinyFrameG'))
  for i in range(4):step();s=check();assert (lng(s,'gTinyFrameMC'),lng(s,'gTinyFrameG'))==frozen
  # Modes restart the aligned stream and resume, including switches from pause.
  h.stdin_cmd('c',settle=.04)
  for key,mode in [('1',1),('2',2),('3',3)]:
   h.tap(key);stop();s=check();assert word(s,'gTinyFrameMode')==mode and word(s,'gTinyPaused')==0
   before=(lng(s,'gTinyFrameMC'),lng(s,'gTinyFrameG'));step();s=check();after=(lng(s,'gTinyFrameMC'),lng(s,'gTinyFrameG'))
   assert after==(before[0]+bool(mode&1),before[1]+bool(mode&2)),(mode,before,after)
   h.stdin_cmd('c',settle=.04)
  # Let both kernels cross the complete message terminator at real frame pace.
  h.wait(len(message)*4/50+1);h.tap('SPACE');stop();s=check();assert word(s,'gTinyPaused')==1
  assert lng(s,'gTinyFrameMC')>169+len(message)*4 and lng(s,'gTinyFrameG')>168+len(message)*4
  h.stdin_cmd('c',settle=.04);h.tap('R');stop();s=check();assert word(s,'gTinyRaster')==1
  missed=lng(s,'gTinyMissedVbl');assert missed==0,(tag,missed)
  h.stdin_cmd('c',settle=.04);h.control('hatari-event keydown 01');h.wait(.3);h.control('hatari-event keyup 01');h.wait(5)
  assert h.mem(addr('gTinyExited'),2).u16(addr('gTinyExited'))==1
  faults=[l for l in h.lines if any(e in l for e in ['Bus Error','Address Error','Illegal instruction'])];assert not faults,faults
  result={'machine':machine,'tos':version,'cpu_mhz':8,'ram_mb':1,'full_screen_checks':checks,'same_text_same_position':True,'all_font_rows':8,'both_pages':True,'mcoder_ring_positions':sorted(mcpos),'griff_ring_positions':sorted(gpos),'all_phases':True,'pause_modes_message_wrap_raster_exit':True,'missed_vbl':missed,'screenshot':shot}
  results.append(result);(root/('analysis/verification-'+tag+'.log')).write_text('\n'.join(h.lines));print(tag,'PASS',checks,'complete screens',flush=True)
(root/('analysis/results'+('-'+sys.argv[1] if len(sys.argv)>1 else '')+'.json')).write_text(json.dumps(results,indent=2)+'\n')
