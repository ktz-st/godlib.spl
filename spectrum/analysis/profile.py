"""Cycle cost of the 199-line palette stream and the entire Timer A handler."""
from pathlib import Path
import json,os,subprocess,sys
os.environ.setdefault('SDL_VIDEODRIVER','dummy');sys.path.insert(0,str(Path.home()/'.codex/skills/hatari-debugging/scripts'))
from hatari_session import HatariSession
from hrdb_profile import Rdb,profile_lines
r=Path(__file__).resolve().parents[1]
sym={p[2]:int(p[0],16) for l in subprocess.check_output(['m68k-atari-mintelf-nm',str(r/'analysis/PDBG.PRG')],text=True).splitlines() if len(p:=l.split())==3}
results=[]
for machine in ('st','ste'):
 with HatariSession(str(r/'SPEC.PRG'),hatari='hatari-hrdb',machine=machine,sound=False,extra_args=['--tos',str(Path.home()/'Atari/tos/TOS v2.06 (1991)(Atari Corp)(Mega-STE)(UK).img'),'--confirm-quit','false','--memsize','1','--cpuclock','8','--cpulevel','0','--monitor','rgb']) as h:
  h.wait(8);base=h.basepage()['text'];db=Rdb()
  db.cmd('break',wait=2);db.cmd('profile 1');db.cmd('run');h.wait(4);db.cmd('break',wait=4)
  msg=db.take('!profile');assert msg;lines=profile_lines(msg);assert lines
  def cost(first,last):return sum(c for a,n,c in lines if base+sym[first]<=a<base+sym[last])
  def calls(n):return sum(count for a,count,c in lines if a==base+sym[n])
  count=calls('Spectrum_TimerA');assert count>20
  stream=cost('Spectrum_Code','Spectrum_CodeEnd')/count
  wrapper=cost('Spectrum_TimerA','Spectrum_TimerAEnd')/count
  result={'machine':machine,'tos':'2.06','cpu_mhz':8,'timer_a_calls':count,'palette_stream_cycles_per_frame':stream,'timer_a_wrapper_and_sync_cycles_per_frame':wrapper,'total_handler_cycles_per_frame':stream+wrapper,'total_handler_ms_at_8mhz':(stream+wrapper)/8000,'pal_frame_budget_percent':100*(stream+wrapper)/160256,'nominal_palette_stream_cycles_including_rts':199*512+16}
  assert abs(stream-(199*512+16))<1500
  (r/('analysis/profile-raw-'+machine+'.json')).write_text(json.dumps({'base':base,'lines':lines}))
  results.append(result);print(json.dumps(result,indent=2),flush=True)
  db.cmd('profile 0');db.cmd('run');db.s.close()
(r/'analysis/profile.json').write_text(json.dumps(results,indent=2)+'\n')
