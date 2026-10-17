"""Verify full frame pixels, fixed castle, both page histories, timing and controls."""
from pathlib import Path
import importlib.util,json,os,struct,subprocess,sys,time
os.environ.setdefault('SDL_VIDEODRIVER','dummy');sys.path.insert(0,str(Path.home()/'.codex/skills/hatari-debugging/scripts'))
from hatari_session import HatariSession
r=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('water_reference',r/'analysis/verify-model.py');model=importlib.util.module_from_spec(spec);spec.loader.exec_module(model)
sym={p[2]:int(p[0],16) for l in subprocess.check_output(['m68k-atari-mintelf-nm',str(r/'analysis/WDBG.PRG')],text=True).splitlines() if len(p:=l.split())==3}
pic=(r/'assets/CASTLE.PI1').read_bytes()[34:];surface=(r/'assets/SURFACE.BIN').read_bytes();states=json.loads((r/'assets/wave.json').read_text())['states']
def expected(tick,active,surf):
 out=bytearray(pic)
 if active:
  st=states[tick];rows=model.reference(st['phase'],st['remaining'])
  for y,source in enumerate(rows,112):out[y*160:(y+1)*160]=pic[source*160:(source+1)*160]
  out[111*160:112*160]=surface[surf*160:(surf+1)*160]
 return out
configs=[('st','2.06','TOS v2.06 (1991)(Atari Corp)(Mega-STE)(UK).img'),('ste','2.06','TOS v2.06 (1991)(Atari Corp)(Mega-STE)(UK).img'),('ste','1.62','TOS v1.62 (1990)(Atari Corp)(STE)(GB)[STE TOS, Rev 2].img')]
if len(sys.argv)>1:configs=[c for c in configs if c[0]+'-'+c[1]==sys.argv[1]]
results=[]
for machine,version,rom in configs:
 label=machine+'-'+version
 with HatariSession(str(r/'WATER.PRG'),machine=machine,sound=False,screenshot_dir=str(r/'analysis/shots'/label/str(int(time.time()))),debug_except='bus,address,illegal',extra_args=['--tos',str(Path.home()/'Atari/tos'/rom),'--confirm-quit','false','--memsize','1','--cpulevel','0','--cpuclock','8','--monitor','rgb']) as h:
  h.wait(8);base=h.basepage()['text']
  def addr(n):return base+sym[n]
  def word(n):
   a=addr(n);return h.mem(a,2).u16(a)
  def setword(n,v):h.debug('w $%x $%02x $%02x'%(addr(n),v>>8,v&255))
  def read(n,size):
   a=addr(n);return h.mem(a,size,paused=True).bytes(a,size)
  def stop():h.debug('b pc = $%x :once'%addr('Screen_Update'));h.wait(.1)
  checks=[];pages=set()
  def check():
   tick=struct.unpack('>H',read('gWaterFrameTick',2))[0]
   active=struct.unpack('>H',read('gWaterFrameEnabled',2))[0]
   surf=struct.unpack('>H',read('gWaterFrameSurface',2))[0]
   page=struct.unpack('>I',read('gWaterScreen',4))[0];pages.add(page)
   path=r/('analysis/frame-'+label+'.bin');h.stdin_cmd('savebin %s $%x $7d00'%(path,page));actual=path.read_bytes();path.unlink()
   want=expected(tick,active,surf)
   assert actual==want,(label,tick,active,surf,next((i,a,b) for i,(a,b) in enumerate(zip(actual,want)) if a!=b))
   assert actual[:111*160]==pic[:111*160]
   checks.append({'tick':tick,'enabled':bool(active),'surface':surf,'page':page})
   return tick
  assert word('gWaterReady')==1
  h.tap('SPACE');assert word('gWaterPaused')==1
  for tick in (0,1,5,9,17,41,63,83):
   setword('gWaterTick',tick);setword('gWaterSurfaceTick',tick%20);stop();assert check()==tick;h.stdin_cmd('c')
  print(label,'PASS all pixels at eight wave phases; castle unchanged',flush=True)
  h.tap('W');assert word('gWaterEnabled')==0;stop();check();h.stdin_cmd('c')
  h.tap('W');assert word('gWaterEnabled')==1;stop();check();h.stdin_cmd('c')
  h.tap('N');assert word('gWaterPaused')==1;stop();assert check()==0;h.stdin_cmd('c')
  for key,speed in [('2',2),('3',4),('1',1)]:h.tap(key);assert word('gWaterSpeed')==speed
  h.tap('SPACE');assert word('gWaterPaused')==0;stop();previous=None
  for frame in range(6):
   tick=check();vbl=struct.unpack('>I',read('gWaterLastVbl',4))[0]
   if previous:assert tick==(previous[0]+vbl-previous[1])%84
   previous=(tick,vbl)
   if frame<5:h.stdin_cmd('b pc = $%x :once'%addr('Screen_Update'))
   h.stdin_cmd('c');h.wait(.1)
  assert len(pages)==2
  shot=h.screenshot()
  h.control('hatari-event keydown 01');h.wait(.3);h.control('hatari-event keyup 01');h.wait(5)
  assert word('gWaterExited')==1
  assert not any(any(e in l for e in ('Bus Error','Address Error','Illegal instruction')) for l in h.lines)
  results.append({'machine':machine,'tos':version,'ram_mb':1,'all_32000_bytes_match':True,'castle_rows_0_to_110_unchanged':True,'both_pages_and_vbl_animation_passed':True,'pause_step_speed_toggle_exit_passed':True,'checks':checks,'screenshot':shot})
  print(label,'PASS both histories, VBL-based animation, controls, exit',flush=True)
(r/('analysis/results'+('-'+sys.argv[1] if len(sys.argv)>1 else '')+'.json')).write_text(json.dumps(results,indent=2)+'\n')
