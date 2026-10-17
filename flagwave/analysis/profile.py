"""Fresh Hatari-HRDB process per mode; CPU cycles and real frame/VBL counts."""
from pathlib import Path
import json,os,subprocess,sys
os.environ.setdefault('SDL_VIDEODRIVER','dummy');sys.path.insert(0,str(Path.home()/'.codex/skills/hatari-debugging/scripts'))
from hatari_session import HatariSession
from hrdb_profile import Rdb,profile_lines
r=Path(__file__).resolve().parents[1]
sym={p[2]:int(p[0],16) for l in subprocess.check_output(['m68k-atari-mintelf-nm',str(r/'analysis/FDBG.PRG')],text=True).splitlines() if len(p:=l.split())==3}
results=[]
for name,keys in [('auto-small',['1']),('auto-default',['2']),('auto-large',['3']),('mouse-still',['M']),('paused',['SPACE'])]:
 with HatariSession(str(r/'FLAG.PRG'),hatari='hatari-hrdb',machine='st',sound=False,extra_args=['--tos',str(Path.home()/'Atari/tos/TOS v2.06 (1991)(Atari Corp)(Mega-STE)(UK).img'),'--confirm-quit','false','--memsize','1','--cpulevel','0','--cpuclock','8','--monitor','rgb']) as h:
  h.wait(8);base=h.basepage()['text']
  for k in keys:h.tap(k)
  h.wait(1);db=Rdb()
  def sample():
   first=min(sym['gFlagLastVbl'],sym['gFlagFrames']);m=h.mem(base+first,8)
   return m.u32(base+sym['gFlagLastVbl']),m.u32(base+sym['gFlagFrames'])
  v0,f0=sample();db.cmd('break',wait=2);db.cmd('profile 1');db.cmd('run');h.wait(4);db.cmd('break',wait=4)
  msg=db.take('!profile');assert msg;lines=profile_lines(msg);assert lines
  def calls(n):return sum(count for a,count,c in lines if a==base+sym[n])
  def cost(first,last):return sum(c for a,n,c in lines if base+sym[first]<=a<base+sym[last])
  draws=calls('Flag_Draw');preps=calls('Flag_Prepare');assert draws>50 and preps>50
  draw=cost('Flag_Draw','Flag_DrawEnd')/draws;prep=cost('Flag_Prepare','Flag_PrepareEnd')/preps
  shifts=calls('Flag_MouseShift');mouse=cost('Flag_MouseShift','Flag_MouseShiftEnd')/draws
  copied=calls('Flag_CopyColumn')/draws
  (r/('analysis/profile-raw-'+name+'.json')).write_text(json.dumps({'base':base,'lines':lines,'draw_calls':draws}))
  db.cmd('profile 0');db.cmd('run');v1,f1=sample();db.s.close()
  result={'mode':name,'machine':'st','tos':'2.06','cpu_mhz':8,'ram_mb':1,'draw_calls':draws,'draw_cycles_per_call':draw,'prepare_cycles_per_call':prep,'mouse_shift_cycles_per_frame':mouse,'kernel_ms':(draw+prep+mouse)/8000,'pal_frame_budget_percent':100*(draw+prep+mouse)/160256,'columns_copied_per_frame':copied,'columns_reused_per_frame':20-copied,'vbl_delta':v1-v0,'frame_delta':f1-f0,'updates_per_second_from_vbl_counters':50*(f1-f0)/(v1-v0)}
  results.append(result);print(json.dumps(result,indent=2),flush=True)
(r/'analysis/profile.json').write_text(json.dumps(results,indent=2)+'\n')
