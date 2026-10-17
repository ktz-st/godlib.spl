"""Measured kernel cost on a stock 8 MHz ST; frame rate from VBL counters."""
from pathlib import Path
import json,os,subprocess,sys
os.environ.setdefault('SDL_VIDEODRIVER','dummy');sys.path.insert(0,str(Path.home()/'.codex/skills/hatari-debugging/scripts'))
from hatari_session import HatariSession
from hrdb_profile import Rdb,profile_lines
r=Path(__file__).resolve().parents[1]
sym={p[2]:int(p[0],16) for l in subprocess.check_output(['m68k-atari-mintelf-nm',str(r/'analysis/RDBG.PRG')],text=True).splitlines() if len(p:=l.split())==3}
with HatariSession(str(r/'REFL.PRG'),hatari='hatari-hrdb',machine='st',sound=False,extra_args=['--tos',str(Path.home()/'Atari/tos/TOS v2.06 (1991)(Atari Corp)(Mega-STE)(UK).img'),'--confirm-quit','false','--memsize','1','--cpulevel','0','--cpuclock','8','--monitor','rgb']) as h:
 h.wait(8);base=h.basepage()['text'];db=Rdb()
 def sample():
  first=min(sym['gReflectLastVbl'],sym['gReflectFrames']);m=h.mem(base+first,8)
  return m.u32(base+sym['gReflectLastVbl']),m.u32(base+sym['gReflectFrames'])
 v0,f0=sample();db.cmd('break',wait=2);db.cmd('profile 1');db.cmd('run');h.wait(4);db.cmd('break',wait=4)
 msg=db.take('!profile');assert msg;lines=profile_lines(msg);assert lines
 calls=sum(n for a,n,c in lines if a==base+sym['Graphic_Reflect']);assert calls>50
 cycles=sum(c for a,n,c in lines if base+sym['Graphic_Reflect']<=a<base+sym['Graphic_Reflect_End'])/calls
 (r/'analysis/profile-raw.json').write_text(json.dumps({'base':base,'calls':calls,'lines':lines}))
 db.cmd('profile 0');db.cmd('run');v1,f1=sample();db.s.close()
 result={'machine':'st','tos':'2.06','cpu_mhz':8,'ram_mb':1,'water_rows':88,'calls':calls,'cycles_per_call':cycles,'kernel_ms':cycles/8000,'pal_frame_budget_percent':100*cycles/160256,'vbl_delta':v1-v0,'frame_delta':f1-f0,'updates_per_second_from_vbl_counters':50*(f1-f0)/(v1-v0)}
 (r/'analysis/profile.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
