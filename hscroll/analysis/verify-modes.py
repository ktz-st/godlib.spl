import sys,subprocess
from pathlib import Path
sys.path.insert(0,str(Path.home()/'.codex/skills/hatari-debugging/scripts'))
from hatari_session import HatariSession
root=Path(__file__).resolve().parent
lines=subprocess.check_output(['m68k-atari-mintelf-nm',str(root/'MODES.PRG')],text=True)
offset=next(int(p[0],16) for line in lines.splitlines() if len(p:=line.split())==3 and p[2]=='gScreenModesResult')
with HatariSession(str(root/'MODES.PRG'),machine='ste',sound=False,debug_except='bus,address,illegal',extra_args=['--memsize','4']) as h:
 h.wait(8);a=h.basepage()['text']+offset; result=h.mem(a,2).u16(a)
 print('screen modes:',result,flush=True);assert result==0
 assert not any('Address Error' in l or 'Bus Error' in l or 'Exception' in l for l in h.lines)
print('PASS: NONE/V/H/H+V, 640x200/320x400/640x400, fixed viewport, alignment, clamp and invalid widths')
