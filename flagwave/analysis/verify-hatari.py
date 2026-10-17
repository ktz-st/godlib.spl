"""Independent rectangle-copy reference; all pixels, clipping and page histories."""
from pathlib import Path
import json,math,os,struct,subprocess,sys,time
os.environ.setdefault('SDL_VIDEODRIVER','dummy');sys.path.insert(0,str(Path.home()/'.codex/skills/hatari-debugging/scripts'))
from hatari_session import HatariSession
r=Path(__file__).resolve().parents[1]
sym={p[2]:int(p[0],16) for l in subprocess.check_output(['m68k-atari-mintelf-nm',str(r/'analysis/FDBG.PRG')],text=True).splitlines() if len(p:=l.split())==3}
pic=(r/'assets/COAST.PI1').read_bytes()[34:]
def expected(offsets):
 out=bytearray(32000)
 for x,dy in enumerate(offsets):
  for sy in range(200):
   y=sy+dy
   if 0<=y<200:out[y*160+x*8:y*160+x*8+8]=pic[sy*160+x*8:sy*160+x*8+8]
 return out
configs=[('st','2.06','TOS v2.06 (1991)(Atari Corp)(Mega-STE)(UK).img'),('ste','2.06','TOS v2.06 (1991)(Atari Corp)(Mega-STE)(UK).img'),('ste','1.62','TOS v1.62 (1990)(Atari Corp)(STE)(GB)[STE TOS, Rev 2].img')]
if len(sys.argv)>1:configs=[c for c in configs if c[0]+'-'+c[1]==sys.argv[1]]
results=[]
for machine,version,rom in configs:
 label=machine+'-'+version
 with HatariSession(str(r/'FLAG.PRG'),machine=machine,sound=False,screenshot_dir=str(r/'analysis/shots'/label/str(int(time.time()))),debug_except='bus,address,illegal',extra_args=['--tos',str(Path.home()/'Atari/tos'/rom),'--confirm-quit','false','--memsize','1','--cpulevel','0','--cpuclock','8','--monitor','rgb']) as h:
  h.wait(8);base=h.basepage()['text'];shot=h.screenshot()
  def addr(n):return base+sym[n]
  def read(n,size):
   a=addr(n);return h.mem(a,size,paused=True).bytes(a,size)
  def word(n):
   a=addr(n);return h.mem(a,2).u16(a)
  def write(n,values):
   b=struct.pack('>'+str(len(values))+'h',*values)
   h.debug('w $%x '%addr(n)+' '.join('$%02x'%v for v in b))
  def stop():h.debug('b pc = $%x :once'%addr('Screen_Update'));h.wait(.1)
  checks=[];pages=set();shifts=set()
  def check(want=None):
   offsets=struct.unpack('>20h',read('gFlagFrameOffsets',40));shifts.update(offsets)
   if want is not None:assert list(offsets)==list(want),(label,offsets,want)
   page=struct.unpack('>I',read('gFlagScreen',4))[0];pages.add(page)
   dump=r/('analysis/frame-'+label+'.bin');h.stdin_cmd('savebin %s $%x $7d00'%(dump,page));actual=dump.read_bytes();dump.unlink()
   target=expected(offsets)
   assert actual==target,(label,next((i,a,b) for i,(a,b) in enumerate(zip(actual,target)) if a!=b))
   checks.append({'offsets':offsets,'page':page});return offsets
  assert word('gFlagReady')==1
  h.tap('SPACE');assert word('gFlagPaused')==1;h.tap('M');assert word('gFlagMode')==0
  patterns=[list(range(-16,4)),list(range(4,17))+[0]*7,[-16,16]*10,[16]*20,[-16]*20,[0]*20]
  for pattern in patterns:
   write('gFlagMouseOffsets',pattern+[0]);stop();check(pattern);h.stdin_cmd('c')
  assert shifts==set(range(-16,17))
  print(label,'PASS all offsets -16..16, all pixels and uncovered edges',flush=True)
  h.tap('A');assert word('gFlagMode')==1
  for key,amp,phase in [('1',4,0),('2',10,63),('3',16,127)]:
   h.tap(key);write('gFlagPhase',[phase]);stop()
   want=[round(amp*math.sin(((phase+(19-x)*12)&255)*math.tau/256)) for x in range(20)]
   check(want);h.stdin_cmd('c')
  for key,speed in [('S',4),('S',8),('S',2)]:h.tap(key);assert word('gFlagSpeed')==speed
  h.tap('M');write('gFlagMouseOffsets',[0]*21)
  # Feed the actual IKBD coordinate read by the program (confirmed +$1e by
  # IKBD_GetMouseY disassembly); stock Hatari has no mouse-motion control event.
  def mouse(y):
   h.debug('w $%x $%02x $%02x'%(addr('gIKBD')+30,(y&65535)>>8,y&255))
  for y,value in [(0,-10),(100,0),(199,9)]:mouse(y);assert word('gFlagMouseInput')==(value&65535)
  for step in range(3):
   h.tap('N');assert word('gFlagPaused')==1;stop()
   # Paused frames redraw the FIFO state after the single shift.
   check([0]*(20-step)+[9]*step)
   history=struct.unpack('>21h',read('gFlagMouseOffsets',42))
   assert history==tuple([0]*(20-step)+[9]*(step+1)),history
   h.stdin_cmd('c')
  print(label,'PASS mouse formula, original FIFO delay, pause and single-step',flush=True)
  h.tap('A');h.tap('2');h.tap('SPACE');assert word('gFlagPaused')==0;stop();previous=None
  for frame in range(6):
   phase=struct.unpack('>H',read('gFlagFramePhase',2))[0]
   want=[round(10*math.sin(((phase+(19-x)*12)&255)*math.tau/256)) for x in range(20)]
   check(want);vbl=struct.unpack('>I',read('gFlagLastVbl',4))[0]
   if previous:assert phase==(previous[0]+2*(vbl-previous[1]))&255
   previous=(phase,vbl)
   if frame<5:h.stdin_cmd('b pc = $%x :once'%addr('Screen_Update'))
   h.stdin_cmd('c');h.wait(.1)
  assert len(pages)==2
  h.control('hatari-event keydown 01');h.wait(.3);h.control('hatari-event keyup 01');h.wait(5)
  assert word('gFlagExited')==1
  faults=[l for l in h.lines if any(e in l for e in ('Bus Error','Address Error','Illegal instruction'))];assert not faults,faults
  result={'machine':machine,'tos':version,'cpu_mhz':8,'ram_mb':1,'full_32000_bytes_match':True,'all_offsets_tested':sorted(shifts),'both_pages_verified':True,'mouse_formula_fifo_and_single_step_passed':True,'auto_vbl_phase_amplitude_speed_pause_exit_passed':True,'checks':checks,'screenshot':shot}
  results.append(result);print(label,'PASS moving frames, page histories, VBL phase, controls and exit',flush=True)
(r/('analysis/results'+('-'+sys.argv[1] if len(sys.argv)>1 else '')+'.json')).write_text(json.dumps(results,indent=2)+'\n')
