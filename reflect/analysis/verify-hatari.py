"""Compare every displayed byte with the decoded Missing Link row algorithm."""
from pathlib import Path
import json,os,struct,subprocess,sys,time
os.environ.setdefault('SDL_VIDEODRIVER','dummy');sys.path.insert(0,str(Path.home()/'.codex/skills/hatari-debugging/scripts'))
from hatari_session import HatariSession
r=Path(__file__).resolve().parents[1]
sym={p[2]:int(p[0],16) for l in subprocess.check_output(['m68k-atari-mintelf-nm',str(r/'analysis/RDBG.PRG')],text=True).splitlines() if len(p:=l.split())==3}
pic=(r/'assets/TOP.PI1').read_bytes()[34:];src=(r/'assets/SOURCE.BIN').read_bytes();steps=[1,1,2,2,2,3,3,4,4,3,3,2,2,1,2,2,1,1,1,0]
def expected(tick):
 out=bytearray(pic);sy=198;phase=((tick+1)//2)%20
 for y in range(88):
  out[(112+y)*160:(113+y)*160]=src[sy*160:(sy+1)*160];sy-=steps[(phase+y)%20]
 return out
configs=[('st','2.06','TOS v2.06 (1991)(Atari Corp)(Mega-STE)(UK).img'),('ste','2.06','TOS v2.06 (1991)(Atari Corp)(Mega-STE)(UK).img'),('ste','1.62','TOS v1.62 (1990)(Atari Corp)(STE)(GB)[STE TOS, Rev 2].img')]
if len(sys.argv)>1:configs=[c for c in configs if c[0]+'-'+c[1]==sys.argv[1]]
results=[]
for machine,version,rom in configs:
 label=machine+'-'+version
 with HatariSession(str(r/'REFL.PRG'),machine=machine,sound=False,screenshot_dir=str(r/'analysis/shots'/label/str(int(time.time()))),debug_except='bus,address,illegal',extra_args=['--tos',str(Path.home()/'Atari/tos'/rom),'--confirm-quit','false','--memsize','1','--cpulevel','0','--cpuclock','8','--monitor','rgb']) as h:
  h.wait(8);base=h.basepage()['text'];shot=h.screenshot()
  def addr(n):return base+sym[n]
  def word(n):
   a=addr(n);return h.mem(a,2).u16(a)
  def setword(n,v):h.debug('w $%x $%02x $%02x'%(addr(n),v>>8,v&255))
  def read(n,size):
   a=addr(n);return h.mem(a,size,paused=True).bytes(a,size)
  def stop():h.debug('b pc = $%x :once'%addr('Screen_Update'));h.wait(.1)
  checks=[];pages=set()
  def check():
   tick=struct.unpack('>H',read('gReflectFrameTick',2))[0]
   state=read('gReflection',18);page=struct.unpack_from('>I',state,4)[0];pages.add(page)
   assert struct.unpack_from('>HH',state,14)==((tick&1)^1,(((tick+1)//2)%20)*2)
   path=r/('analysis/frame-'+label+'.bin');h.stdin_cmd('savebin %s $%x $7d00'%(path,page));actual=path.read_bytes();path.unlink()
   want=expected(tick)
   assert actual==want,(label,tick,next((i,a,b) for i,(a,b) in enumerate(zip(actual,want)) if a!=b))
   checks.append({'tick':tick,'page':page});return tick
  assert word('gReflectReady')==1
  h.tap('SPACE');assert word('gReflectPaused')==1
  for tick in (0,1,2,17,38,39):
   setword('gReflectTick',tick);stop();assert check()==tick;h.stdin_cmd('c')
  h.tap('N');stop();assert check()==0;h.stdin_cmd('c')
  h.tap('SPACE');assert word('gReflectPaused')==0;stop();previous=None
  for frame in range(6):
   tick=check()
   if previous is not None:assert tick==(previous+1)%40
   previous=tick
   if frame<5:h.stdin_cmd('b pc = $%x :once'%addr('Screen_Update'))
   h.stdin_cmd('c');h.wait(.1)
  assert len(pages)==2
  h.control('hatari-event keydown 01');h.wait(.3);h.control('hatari-event keyup 01');h.wait(5)
  assert word('gReflectExited')==1
  faults=[l for l in h.lines if any(e in l for e in ('Bus Error','Address Error','Illegal instruction'))]
  assert not faults,faults
  result={'filename':'REFL.PRG','machine':machine,'tos':version,'cpu_mhz':8,'ram_mb':1,'all_32000_bytes_match':True,'castle_rows_0_to_111_unchanged':True,'both_pages_verified':True,'pause_step_wrap_exit_passed':True,'checks':checks,'screenshot':shot}
  results.append(result);print(label,'PASS pixels, state, both pages, animation, controls and exit',flush=True)
(r/('analysis/results'+('-'+sys.argv[1] if len(sys.argv)>1 else '')+'.json')).write_text(json.dumps(results,indent=2)+'\n')
