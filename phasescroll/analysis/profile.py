"""STe 8 MHz instruction cycles, including BLiTTER HOG stalls and raster ISR."""
from pathlib import Path
import json,os,subprocess,sys
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
sys.path.insert(0,str(Path.home()/'.agents/skills/hatari-debugging/scripts'))
from hatari_session import HatariSession
from hrdb_profile import Rdb,profile_lines
root=Path(__file__).resolve().parents[1]
sym={p[2]:int(p[0],16) for l in subprocess.check_output(['m68k-atari-mintelf-nm',str(root/'analysis/PDBG.PRG')],text=True).splitlines() if len(p:=l.split())==3}
rom=Path.home()/'Atari/tos/TOS v2.06 (1991)(Atari Corp)(Mega-STE)(UK).img'
results=[]
for key,speed in [('1',1),('2',2),('4',4),('8',8),('0',0)]:
 with HatariSession(str(root/'PHASE.PRG'),hatari='hatari-hrdb',machine='ste',sound=False,extra_args=['--tos',str(rom),'--confirm-quit','false','--memsize','1','--cpuclock','8','--cpulevel','0','--monitor','rgb']) as h:
  h.wait(8);base=h.basepage()['text']
  if key=='8':h.control('hatari-event keydown 8');h.wait(.15);h.control('hatari-event keyup 8')
  else:h.tap(key)
  a=base+sym['gPhaseMagnitude'];assert h.mem(a,2).u16(a)==speed
  def sample():
   a=base+min(sym['gPhaseLastVbl'],sym['gPhaseFrames']);b=base+max(sym['gPhaseLastVbl'],sym['gPhaseFrames'])+4;m=h.mem(a,b-a)
   return m.u32(base+sym['gPhaseLastVbl']),m.u32(base+sym['gPhaseFrames'])
  v0,f0=sample();db=Rdb();db.cmd('break',wait=2);db.cmd('profile 1');db.cmd('run');h.wait(4);db.cmd('break',wait=4)
  msg=db.take('!profile');assert msg;lines=profile_lines(msg);assert lines
  def calls(n):return sum(nc for a,nc,c in lines if a==base+sym[n])
  def cost(first,last):return sum(c for a,n,c in lines if base+sym[first]<=a<base+sym[last])
  frames=calls('Phase_Step');assert frames>100
  kernel=cost('Phase_Init','Phase_KernelEnd')/frames
  raster=cost('HSplit_TimerB','HSplit_TimerBEnd')/calls('HSplit_TimerB')
  (root/('analysis/profile-raw-'+key+'.json')).write_text(json.dumps({'base':base,'lines':lines,'phase_calls':frames}))
  db.cmd('profile 0');db.cmd('run');v1,f1=sample();db.s.close()
  result={'speed_pixels':speed,'machine':'ste','tos':'2.06','cpu_mhz':8,'ram_mb':1,'phase_calls':frames,'phase_cycles_per_update':kernel,'phase_ms':kernel/8000,'phase_pal_frame_percent':100*kernel/160256,'split_cycles_per_frame':raster,'split_ms':raster/8000,'phase_plus_split_pal_frame_percent':100*(kernel+raster)/160256,'updates_per_second_from_vbl_counters':50*(f1-f0)/(v1-v0)}
  results.append(result);print(json.dumps(result,indent=2),flush=True)
(root/'analysis/profile.json').write_text(json.dumps(results,indent=2)+'\n')
