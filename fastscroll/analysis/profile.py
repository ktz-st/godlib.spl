"""Measure the active 68000 shift/draw kernels with hrdb, default and top speed."""
from pathlib import Path
import json,os,subprocess,sys
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
sys.path.insert(0,str(Path.home()/'.codex/skills/hatari-debugging/scripts'))
from hatari_session import HatariSession
from hrdb_profile import Rdb,profile_lines
root=Path(__file__).resolve().parents[1]
sym={p[2]:int(p[0],16) for l in subprocess.check_output(['m68k-atari-mintelf-nm',str(root/'analysis/FDBG.PRG')],text=True).splitlines() if len(p:=l.split())==3}
rom='/Users/kriss/Atari/tos/TOS v2.06 (1991)(Atari Corp)(Mega-STE)(UK).img'
results=[]
with HatariSession(str(root/'FSCRL.PRG'),hatari='hatari-hrdb',machine='st',sound=False,extra_args=['--tos',rom,'--confirm-quit','false','--memsize','1','--cpuclock','8','--cpulevel','0','--monitor','rgb']) as h:
 h.wait(8);base=h.basepage()['text'];r=Rdb()
 for key,speed in [('3',4),('4',8)]:
  h.tap(key);r.cmd('break',wait=1);r.cmd('profile 1');r.cmd('run');h.wait(3);r.cmd('break',wait=2)
  lines=profile_lines(r.take('!profile'));assert lines
  def cost(first,last):return sum(c for a,n,c in lines if base+sym[first]<=a<base+sym[last])
  frames=sum(n for a,n,c in lines if a==base+sym['Scroll_Draw']);assert frames>0
  shift=cost('Scroll_Shift','Scroll_ShiftEnd');draw=cost('Scroll_Draw','Scroll_DrawEnd');insert=cost('Scroll_Insert','Scroll_Draw')
  total=sum(c for a,n,c in lines)
  results.append({'speed_pixels':speed,'draw_calls':frames,'profile_cycles':total,'shift_cycles_per_frame':shift/frames,'draw_cycles_per_frame':draw/frames,'shift_draw_insert_cycles_per_frame':(shift+draw+insert)/frames,'kernel_percent_of_50hz_budget':100*(shift+draw+insert)/frames/160000})
  r.cmd('profile 0');r.cmd('run')
 r.s.close()
(root/'analysis/profile.json').write_text(json.dumps(results,indent=2)+'\n');print(json.dumps(results,indent=2),flush=True)
