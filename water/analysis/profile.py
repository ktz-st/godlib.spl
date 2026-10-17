"""Fresh ST hrdb process for each mode; cycles and target frame/VBL counters."""
from pathlib import Path
import json,os,subprocess,sys
os.environ.setdefault('SDL_VIDEODRIVER','dummy');sys.path.insert(0,str(Path.home()/'.codex/skills/hatari-debugging/scripts'))
from hatari_session import HatariSession
from hrdb_profile import Rdb,profile_lines
r=Path(__file__).resolve().parents[1]
sym={p[2]:int(p[0],16) for l in subprocess.check_output(['m68k-atari-mintelf-nm',str(r/'analysis/WDBG.PRG')],text=True).splitlines() if len(p:=l.split())==3}
results=[]
for name,key in [('normal','1'),('fast','3'),('off','W')]:
 with HatariSession(str(r/'WATER.PRG'),hatari='hatari-hrdb',machine='st',sound=False,extra_args=['--tos',str(Path.home()/'Atari/tos/TOS v2.06 (1991)(Atari Corp)(Mega-STE)(UK).img'),'--confirm-quit','false','--memsize','1','--cpulevel','0','--cpuclock','8','--monitor','rgb']) as h:
  h.wait(8);base=h.basepage()['text'];h.tap(key);h.wait(.5);db=Rdb()
  def sample():
   first=min(sym['gWaterLastVbl'],sym['gWaterFrames']);m=h.mem(base+first,8)
   return m.u32(base+sym['gWaterLastVbl']),m.u32(base+sym['gWaterFrames'])
  v0,f0=sample();db.cmd('break',wait=2);db.cmd('profile 1');db.cmd('run');h.wait(4);db.cmd('break',wait=4)
  msg=db.take('!profile');assert msg;lines=profile_lines(msg);assert lines
  def calls(n):return sum(count for a,count,c in lines if a==base+sym[n])
  def cost(first,last):return sum(c for a,n,c in lines if base+sym[first]<=a<base+sym[last])
  draws=calls('Water_Draw');commands=calls('Commands');assert draws>50 and commands>50
  draw=cost('Water_Draw','Water_DrawEnd')/draws;prep=cost('Commands','GodLib_Game_Main')/commands
  copy=sum(calls(n) for n in sym if n.startswith('Water_CopyRow'))/draws
  skip=sum(calls(n) for n in sym if n.startswith('Water_SkipRow'))/draws
  assert abs(copy+skip-88)<1
  (r/('analysis/profile-raw-'+name+'.json')).write_text(json.dumps({'base':base,'draws':draws,'commands':commands,'lines':lines}))
  db.cmd('profile 0');db.cmd('run');v1,f1=sample();db.s.close()
  result={'mode':name,'machine':'st','tos':'2.06','cpu_mhz':8,'ram_mb':1,'draw_calls':draws,'draw_cycles_per_call':draw,'command_cycles_per_call':prep,'kernel_and_commands_ms':(draw+prep)/8000,'pal_frame_budget_percent':100*(draw+prep)/160256,'water_rows_copied_per_frame':copy,'water_rows_reused_per_frame':skip,'surface_row_copies_per_frame':calls('Water_SurfaceCopy')/draws,'vbl_delta':v1-v0,'frame_delta':f1-f0,'updates_per_second_from_vbl_counters':50*(f1-f0)/(v1-v0)}
  results.append(result);print(json.dumps(result,indent=2),flush=True)
(r/'analysis/profile.json').write_text(json.dumps(results,indent=2)+'\n')
