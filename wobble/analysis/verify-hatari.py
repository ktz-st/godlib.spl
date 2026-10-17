"""Compare all 32000 displayed bytes with independent planar shift references."""
from pathlib import Path
import json,math,os,struct,subprocess,sys,time
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
sys.path.insert(0,str(Path.home()/'.codex/skills/hatari-debugging/scripts'))
from hatari_session import HatariSession
root=Path(__file__).resolve().parents[1]
sym={p[2]:int(p[0],16) for l in subprocess.check_output(['m68k-atari-mintelf-nm',str(root/'analysis/WDBG.PRG')],text=True).splitlines() if len(p:=l.split())==3}
b=(root/'assets/COAST.PI1').read_bytes();mask=(1<<320)-1
planes=[[int.from_bytes(b''.join(b[34+y*160+g*8+p*2:36+y*160+g*8+p*2] for g in range(20)),'big') for p in range(4)] for y in range(200)]
sine=[round(16*math.sin(i*math.tau/256)) for i in range(256)]
def reference(amp,phase):
 expected=bytearray()
 for y in range(200):
  dx=0 if amp==0 else sine[(phase+y*2)&255]//(16//amp)
  row=[((v>>dx) if dx>=0 else (v<<(-dx))&mask).to_bytes(40,'big') for v in planes[y]]
  for g in range(20):
   for p in range(4):expected+=row[p][g*2:g*2+2]
 return expected
tos206=os.environ.get('HATARI_TOS','/Users/kriss/Atari/tos/TOS v2.06 (1991)(Atari Corp)(Mega-STE)(UK).img')
tos162=os.environ.get('HATARI_TOS162','/Users/kriss/Atari/tos/TOS v1.62 (1990)(Atari Corp)(STE)(GB)[STE TOS, Rev 2].img')
configs=[('st','2.06',tos206),('ste','2.06',tos206),('ste','1.62',tos162)]
if len(sys.argv)>1:configs=[c for c in configs if c[0]+'-'+c[1]==sys.argv[1]]
results=[]
for machine,version,tos in configs:
 label=machine+'-'+version;shots=root/'analysis/shots'/label/str(int(time.time()))
 with HatariSession(str(root/'WOBBLE.PRG'),machine=machine,sound=False,screenshot_dir=str(shots),debug_except='bus,address,illegal',extra_args=['--tos',tos,'--confirm-quit','false','--memsize','1','--cpulevel','0','--cpuclock','8','--monitor','rgb']) as h:
  h.wait(10);base=h.basepage()['text']
  def addr(n):return base+sym[n]
  def raw(n,size,paused=False):return h.mem(addr(n),size,paused=paused).bytes(addr(n),size)
  def word(n):return struct.unpack('>H',raw(n,2))[0]
  def setword(n,v):h.debug('w $%x $%02x $%02x'%(addr(n),v>>8,v&255))
  assert word('gWobbleReady')==1
  h.tap('SPACE');assert word('gWobblePaused')==1
  shifts=set()
  for key,amp,phase in [('0',0,0),('1',4,17),('2',8,63),('3',16,91)]:
   h.tap(key);assert word('gWobbleAmplitude')==amp;setword('gWobblePhase',phase)
   h.debug('b pc = $%x :once'%addr('Screen_Update'));h.wait(.1)
   assert struct.unpack('>H',raw('gWobbleFramePhase',2,True))[0]==phase
   page=struct.unpack('>I',raw('gWobbleScreen',4,True))[0];dump=root/('analysis/screen-'+label+'.bin')
   h.stdin_cmd('savebin %s $%x $7d00'%(dump,page));actual=dump.read_bytes();dump.unlink()
   expected=reference(amp,phase)
   shifts.update(0 if amp==0 else sine[(phase+y*2)&255]//(16//amp) for y in range(200))
   assert actual==expected,(label,amp,phase,next(i for i,(a,b) in enumerate(zip(actual,expected)) if a!=b))
   h.stdin_cmd('c');shot=h.screenshot();print(label,'PASS full image amplitude',amp,'phase',phase,shot,flush=True)
  assert shifts==set(range(-16,17))
  for expected in (16,4,8):h.tap('S');assert word('gWobbleSpeed')==expected
  h.tap('SPACE');assert word('gWobblePaused')==0;h.wait(1)
  # Consecutive moving frames exercise both history pages and VBL-based phase.
  h.debug('b pc = $%x :once'%addr('Screen_Update'));h.wait(.1)
  previous=None;moving=[];pages=set()
  for frame in range(6):
   phase=struct.unpack('>H',raw('gWobbleFramePhase',2,True))[0]
   amp=struct.unpack('>H',raw('gWobbleFrameAmplitude',2,True))[0]
   vbl=struct.unpack('>I',raw('gWobbleLastVbl',4,True))[0]
   page=struct.unpack('>I',raw('gWobbleScreen',4,True))[0];pages.add(page)
   dump=root/('analysis/moving-'+label+'.bin')
   h.stdin_cmd('savebin %s $%x $7d00'%(dump,page));actual=dump.read_bytes();dump.unlink()
   assert actual==reference(amp,phase),(label,frame,'moving image / history')
   if previous:assert phase==(previous[0]+8*(vbl-previous[1]))&255,(label,phase,previous,vbl)
   previous=(phase,vbl);moving.append({'phase':phase,'vbl':vbl,'page':page})
   if frame<5:h.stdin_cmd('b pc = $%x :once'%addr('Screen_Update'))
   h.stdin_cmd('c');h.wait(.1)
  assert len(pages)==2
  print(label,'PASS moving frames, both history pages and VBL-based phase',flush=True)
  h.control('hatari-event keydown 01');h.wait(.3);h.control('hatari-event keyup 01');h.wait(5)
  assert word('gWobbleExited')==1
  assert not any(any(e in l for e in ('Bus Error','Address Error','Illegal instruction')) for l in h.lines)
  results.append({'machine':machine,'tos':version,'ram_mb':1,'all_image_bytes_match':True,'amplitudes':[0,4,8,16],'horizontal_offsets_checked':sorted(shifts),'pause_speed_resume_exit':True,'moving_frames':moving,'vbl_based_phase_verified':True})
(root/('analysis/results'+('-'+sys.argv[1] if len(sys.argv)>1 else '')+'.json')).write_text(json.dumps(results,indent=2)+'\n')
