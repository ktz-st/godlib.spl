from pathlib import Path
import os,sys,subprocess,json
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
sys.path.insert(0,str(Path.home()/'.agents/skills/hatari-debugging/scripts'))
from hatari_session import HatariSession
root=Path(__file__).resolve().parents[1]
sym={p[2]:int(p[0],16) for l in subprocess.check_output(['m68k-atari-mintelf-nm',str(root/'analysis/CHKDBG.PRG')],text=True).splitlines() if len(p:=l.split())==3}
with HatariSession(str(root/'CHKFX.PRG'),machine='ste',sound=False,debug_except='bus,address,illegal',extra_args=['--tos',str(Path.home()/'Atari/tos/TOS v1.62 (1990)(Atari Corp)(STE)(GB)[STE TOS, Rev 2].img'),'--confirm-quit','false','--memsize','1','--cpuclock','8']) as h:
 h.wait(8);base=h.basepage()['text'];h.control('hatari-event keydown 01');h.wait(.2);h.control('hatari-event keyup 01');h.wait(2)
 faults=[l for l in h.lines if any(e in l for e in ['Bus Error','Address Error','Illegal instruction'])]
 if faults:
  h.debug('r');h.debug('d $e1fc70 $e1fcd0')
 (root/'analysis/exit-diagnostic.log').write_text('\n'.join(h.lines))
 print('faults',faults,flush=True)
 assert not faults,faults
 assert h.mem(base+sym['gCheckerExited'],2).u16(base+sym['gCheckerExited'])==1
 print('PASS clean exit without the raster marker',flush=True)
