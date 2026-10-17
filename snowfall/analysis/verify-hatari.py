"""Check snow conservation, static planes, controls and clean exit on ST/STE."""
from pathlib import Path
import json,os,struct,subprocess,sys,time
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
sys.path.insert(0,str(Path.home()/'.codex/skills/hatari-debugging/scripts'))
from hatari_session import HatariSession
root=Path(__file__).resolve().parents[1]
nm=subprocess.check_output(['m68k-atari-mintelf-nm',str(root/'analysis/SDBG.PRG')],text=True)
syms={p[2]:int(p[0],16) for l in nm.splitlines() if len(p:=l.split())==3}
rom206=os.environ.get('HATARI_TOS','/Users/kriss/Atari/tos/TOS v2.06 (1991)(Atari Corp)(Mega-STE)(UK).img')
rom162=os.environ.get('HATARI_TOS162','/Users/kriss/Atari/tos/TOS v1.62 (1990)(Atari Corp)(STE)(GB)[STE TOS, Rev 2].img')
configs=[('st','2.06',rom206),('ste','2.06',rom206),('ste','1.62',rom162)]
if len(sys.argv)>1:configs=[c for c in configs if c[0]+'-'+c[1]==sys.argv[1]]
results=[]
for machine,version,rom in configs:
 label=machine+'-'+version;shots=root/'analysis/shots'/label/str(int(time.time()))
 with HatariSession(str(root/'SNOW.PRG'),machine=machine,sound=False,screenshot_dir=str(shots),debug_except='bus,address,illegal',extra_args=['--confirm-quit','false','--memsize','1','--cpulevel','0','--cpuclock','8','--monitor','rgb','--tos',rom]) as h:
  h.wait(8);base=h.basepage()['text']
  def addr(n):return base+syms[n]
  def raw(n,size):return h.mem(addr(n),size).bytes(addr(n),size)
  def word(n):return struct.unpack('>H',raw(n,2))[0]
  def steps():return struct.unpack('>I',raw('gSnowSteps',4))[0]
  assert word('gSnowReady')==1
  before=steps();h.wait(.2);assert steps()>before
  h.tap('SPACE');assert word('gSnowPaused')==1
  n=steps();h.wait(.2);assert steps()==n
  def snapshot():
   h.debug('b pc = $%x :once'%addr('Vbl_WaitVbl'));h.wait(.2)
   a=addr('gSnowScreen');page=h.mem(a,4,paused=True).u32(a)
   dump=root/('analysis/screen-'+label+'.bin')
   h.stdin_cmd('savebin %s $%x $7d00'%(dump,page))
   b=dump.read_bytes();dump.unlink();h.stdin_cmd('c');assert len(b)==32000
   return b
  def planes(b):
   words=struct.unpack('>16000H',b)
   static=tuple(words[i] for i in range(16000) if i%4!=3)
   snow=words[3::4]
   return static,sum(w.bit_count() for w in snow),sum((i//20)*w.bit_count() for i,w in enumerate(snow))
  a=snapshot();static,count,gravity=planes(a);assert count>120
  h.tap('S');assert steps()==n+1
  b=snapshot();other,count2,gravity2=planes(b)
  assert static==other and count==count2 and gravity2>=gravity
  assert a!=b and gravity2>gravity
  # Full bottom and side walls remain solid, no snow crosses the viewport.
  for y in range(24,200):
   left,right=struct.unpack_from('>H',b,y*160)[0],struct.unpack_from('>H',b,y*160+152)[0]
   assert left&0x8000 and right&1
  h.screenshot()
  for key,value in [('1',4),('2',8),('3',16)]:h.tap(key);assert word('gSnowDensity')==value
  h.tap('C');assert steps()==0;assert word('gSnowPaused')==1
  assert planes(snapshot())[1]<=120
  h.tap('SPACE');assert word('gSnowPaused')==0;h.wait(2);assert steps()>0
  h.screenshot()
  h.control('hatari-event keydown 01');h.wait(.3);h.control('hatari-event keyup 01');h.wait(5)
  assert word('gSnowExited')==1
  assert not any(any(e in l for e in ('Bus Error','Address Error','Illegal instruction')) for l in h.lines)
  print(label,'PASS static planes, snow conservation, fall, controls, exit',flush=True)
  results.append({'machine':machine,'tos':version,'ram_mb':1,'static_planes_unchanged':True,'snow_conserved_on_single_step':True,'snow_moves_down':True,'pause_density_clear_exit':True,'snow_pixels':count})
(root/('analysis/results'+('-'+sys.argv[1] if len(sys.argv)>1 else '')+'.json')).write_text(json.dumps(results,indent=2)+'\n')
