"""Compare real planar RAM against an independent affine stripe formula."""
from pathlib import Path
import json,os,struct,subprocess,sys,time
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
sys.path.insert(0,str(Path.home()/'.agents/skills/hatari-debugging/scripts'))
from hatari_session import HatariSession
root=Path(__file__).resolve().parents[1]
sym={p[2]:int(p[0],16) for l in subprocess.check_output(['m68k-atari-mintelf-nm',str(root/'analysis/CHKDBG.PRG')],text=True).splitlines() if len(p:=l.split())==3}
params=list(struct.iter_unpack('>iiiH',(root/'assets/PARAMS.BIN').read_bytes()))
configs=[('st','2.06','TOS v2.06 (1991)(Atari Corp)(Mega-STE)(UK).img'),('ste','2.06','TOS v2.06 (1991)(Atari Corp)(Mega-STE)(UK).img'),('ste','1.62','TOS v1.62 (1990)(Atari Corp)(STE)(GB)[STE TOS, Rev 2].img')]
if len(sys.argv)>1:configs=[c for c in configs if c[0]+'-'+c[1]==sys.argv[1]]
results=[]
for machine,version,rom in configs:
 tag=machine+'-'+version
 with HatariSession(str(root/'CHKFX.PRG'),machine=machine,sound=False,screenshot_dir=str(root/'analysis/shots'/tag/str(int(time.time()))),debug_except='bus,address,illegal',extra_args=['--tos',str(Path.home()/'Atari/tos'/rom),'--confirm-quit','false','--memsize','1','--cpuclock','8','--cpulevel','0','--monitor','rgb']) as h:
  h.wait(8);base=h.basepage()['text'];shot=h.screenshot()
  def addr(n):return base+sym[n]
  def stop():h.debug('b pc = $%x :once'%addr('Screen_Update'))
  def dump(a,size,name):
   p=root/('analysis/temp-'+tag+'-'+name+'.bin');p.unlink(missing_ok=True)
   h.stdin_cmd('savebin %s $%x $%x'%(p,a,size),settle=.03)
   for i in range(200):
    if p.exists() and p.stat().st_size==size:break
    time.sleep(.01)
   data=p.read_bytes();assert len(data)==size;p.unlink();return data
  first=min(v for k,v in sym.items() if k.startswith('gChecker'));last=max(v+4 for k,v in sym.items() if k.startswith('gChecker'))
  def state():return dump(base+first,last-first,'state')
  def word(s,n):return struct.unpack_from('>H',s,sym[n]-first)[0]
  def lng(s,n):return struct.unpack_from('>I',s,sym[n]-first)[0]
  def step():h.stdin_cmd('b pc = $%x :once'%addr('Screen_Update'),settle=.02);h.stdin_cmd('c',settle=.04)
  stop();s=state();assert word(s,'gCheckerReady')==1
  bgptr=struct.unpack('>I',dump(addr('gScreenClass')+12,4,'backptr'))[0];background=dump(bgptr,32000,'background')
  phases=set();pages=set();checks=0
  def check():
   global checks
   s=state();phase=word(s,'gCheckerFramePhase');page=lng(s,'gCheckerScreen');want=bytearray(background)
   for y in range(96):
    for x in range(320):
     colour=0
     for initial,dy,spacing,p in params[phase*2:phase*2+2]:colour^=bool(p)^(((x*256-initial-y*dy)//spacing+1)&1)
     if colour:want[(56+y)*160+(x//16)*8+(x&15)//8]|=128>>(x&7)
   actual=dump(page,32000,'screen')
   assert actual==want,(tag,phase,next(((i,a,b) for i,(a,b) in enumerate(zip(actual,want)) if a!=b),None))
   phases.add(phase);pages.add(page);checks+=1;return s
  for i in range(128 if machine=='st' else 64):
   check();step()
   if i%64==63:print(tag,'PASS screens',checks,flush=True)
  if machine=='st':assert len(phases)==128
  assert len(pages)==2
  h.stdin_cmd('c',settle=.03);h.tap('SPACE');stop();s=check();assert word(s,'gCheckerPaused')==1
  frozen=word(s,'gCheckerFramePhase')
  for i in range(3):step();s=check();assert word(s,'gCheckerFramePhase')==frozen
  h.stdin_cmd('c',settle=.03);h.tap('3');h.tap('D');h.tap('R');stop();s=check()
  assert word(s,'gCheckerSpeed')==4 and word(s,'gCheckerDirection')==65535 and word(s,'gCheckerRaster')==1
  h.stdin_cmd('c',settle=.03);h.tap('SPACE');stop();s=check();before=word(s,'gCheckerFramePhase');step();s=check();assert word(s,'gCheckerFramePhase')==(before-4)&127
  missed=lng(s,'gCheckerMissedVbl');assert missed==0,(tag,missed)
  h.stdin_cmd('c',settle=.03);h.control('hatari-event keydown 01');h.wait(.2);h.control('hatari-event keyup 01');h.wait(4)
  assert h.mem(addr('gCheckerExited'),2).u16(addr('gCheckerExited'))==1
  (root/('analysis/verification-'+tag+'.log')).write_text('\n'.join(h.lines))
  faults=[l for l in h.lines if any(e in l for e in ['Bus Error','Address Error','Illegal instruction'])]
  assert not faults,faults
  result={'machine':machine,'tos':version,'cpu_mhz':8,'ram_mb':1,'full_screen_checks':checks,'unique_phases':len(phases),'both_pages':True,'pause_speed_direction_raster_exit':True,'missed_vbl':missed,'screenshot':shot}
  (root/('analysis/results-'+tag+'.json')).write_text(json.dumps(result,indent=2)+'\n');results.append(result);print(tag,'PASS',result,flush=True)
(root/'analysis/results.json').write_text(json.dumps(results,indent=2)+'\n')
