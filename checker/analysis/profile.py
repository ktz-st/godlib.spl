"""Measure the ASM raster kernel with precomputed geometry, with no timing marker."""
from pathlib import Path
import json,os,subprocess,sys
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
sys.path.insert(0,str(Path.home()/'.agents/skills/hatari-debugging/scripts'))
from hatari_session import HatariSession
from hrdb_profile import Rdb,profile_lines
root=Path(__file__).resolve().parents[1]
sym={p[2]:int(p[0],16) for l in subprocess.check_output(['m68k-atari-mintelf-nm',str(root/'analysis/CHKDBG.PRG')],text=True).splitlines() if len(p:=l.split())==3}
rom=Path.home()/'Atari/tos/TOS v2.06 (1991)(Atari Corp)(Mega-STE)(UK).img'
with HatariSession(str(root/'CHKFX.PRG'),hatari='hatari-hrdb',machine='st',sound=False,extra_args=['--tos',str(rom),'--confirm-quit','false','--memsize','1','--cpuclock','8','--cpulevel','0','--monitor','rgb']) as h:
 h.wait(8);base=h.basepage()['text']
 def sample():
  a=base+sym['gCheckerLastVbl'];m=h.mem(a,8);return m.u32(a),m.u32(a+4)
 v0,f0=sample();db=Rdb();db.cmd('break',wait=2);db.cmd('profile 1');db.cmd('run');h.wait(6);db.cmd('break',wait=4)
 msg=db.take('!profile');assert msg;lines=profile_lines(msg);assert lines
 data=[]
 for kernel in ['Checker_Draw']:
  count=sum(n for a,n,c in lines if a==base+sym[kernel]);assert count>40
  cost=sum(c for a,n,c in lines if base+sym[kernel]<=a<base+sym[kernel+'End'])/count
  data.append({'kernel':kernel,'calls':count,'cycles_per_frame':cost,'ms':cost/8000,'pal_frame_percent':100*cost/160256})
 (root/'analysis/profile-raw.json').write_text(json.dumps({'base':base,'lines':lines}))
 db.cmd('profile 0');db.cmd('run');v1,f1=sample();db.s.close()
 result={'machine':'st','tos':'2.06','cpu_mhz':8,'ram_mb':1,'viewport':[320,96],'kernel_costs':data,'total_cycles_per_frame':sum(d['cycles_per_frame'] for d in data),'updates_per_second_from_vbl':50*(f1-f0)/(v1-v0)}
 (root/'analysis/profile.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2),flush=True)
