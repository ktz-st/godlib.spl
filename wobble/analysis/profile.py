"""Fresh emulator per amplitude: MOVEM copy/skip costs and target VBL counters."""
from pathlib import Path
import json,os,subprocess,sys
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
sys.path.insert(0,str(Path.home()/'.codex/skills/hatari-debugging/scripts'))
from hatari_session import HatariSession
from hrdb_profile import Rdb,profile_lines
root=Path(__file__).resolve().parents[1]
sym={p[2]:int(p[0],16) for l in subprocess.check_output(['m68k-atari-mintelf-nm',str(root/'analysis/WDBG.PRG')],text=True).splitlines() if len(p:=l.split())==3}
rom='/Users/kriss/Atari/tos/TOS v2.06 (1991)(Atari Corp)(Mega-STE)(UK).img'
results=[]
for key,amp in [('0',0),('2',8),('3',16)]:
 with HatariSession(str(root/'WOBBLE.PRG'),hatari='hatari-hrdb',machine='st',sound=False,extra_args=['--tos',rom,'--confirm-quit','false','--memsize','1','--cpuclock','8','--cpulevel','0','--monitor','rgb']) as h:
  h.wait(10);base=h.basepage()['text'];h.tap(key);h.wait(.5);r=Rdb()
  def sample():
   first=min(sym['gWobbleLastVbl'],sym['gWobbleFrames']);m=h.mem(base+first,8)
   return m.u32(base+sym['gWobbleLastVbl']),m.u32(base+sym['gWobbleFrames'])
  v0,f0=sample()
  r.cmd('break',wait=2);r.cmd('profile 1');r.cmd('run');h.wait(4);r.cmd('break',wait=4)
  msg=r.take('!profile');assert msg;lines=profile_lines(msg);assert lines
  def cost(first,last):return sum(c for a,n,c in lines if base+sym[first]<=a<base+sym[last])
  def calls(n):return sum(count for a,count,c in lines if a==base+sym[n])
  draws=calls('Wobble_Draw');commands=calls('Commands');assert draws>0 and commands>0
  draw=cost('Wobble_Draw','Wobble_DrawEnd')/draws;prep=cost('Commands','GodLib_Game_Main')/commands
  copied=sum(calls(n) for n in sym if n.startswith('Wobble_CopyRow'))/draws
  skipped=sum(calls(n) for n in sym if n.startswith('Wobble_SkipRow'))/draws
  (root/('analysis/profile-raw-'+str(amp)+'.json')).write_text(json.dumps({'base':base,'draws':draws,'commands':commands,'lines':lines}))
  r.cmd('profile 0');r.cmd('run');v1,f1=sample();assert v1>v0 and f1>f0
  results.append({'amplitude_pixels':amp,'phase_speed_per_vbl':8,'draw_calls':draws,'commands_calls':commands,'draw_cycles_per_call':draw,'command_cycles_per_call':prep,'draw_and_commands_ms_at_8mhz':(draw+prep)/8000,'equivalent_percent_of_one_50hz_pal_frame':100*(draw+prep)/160256,'average_rows_copied_per_call':copied,'average_rows_reused_per_call':skipped,'target_vbl_delta':v1-v0,'target_frame_delta':f1-f0,'updates_per_second_from_vbl_counters':50*(f1-f0)/(v1-v0)})
  r.s.close();print(json.dumps(results[-1],indent=2),flush=True)
(root/'analysis/profile.json').write_text(json.dumps(results,indent=2)+'\n')
