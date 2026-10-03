import subprocess,sys
from pathlib import Path
sys.path.insert(0,str(Path.home()/'.codex/skills/hatari-debugging/scripts'))
from hatari_session import HatariSession
root=Path(__file__).resolve().parents[1]
lines=subprocess.check_output(['m68k-atari-mintelf-nm','-n',str(root/'analysis/CHUNKDBG.TOS')],text=True)
syms={p[2]:int(p[0],16) for line in lines.splitlines() if len(p:=line.split())==3}
with HatariSession(str(root/'CHUNKY.TOS'),screenshot_dir=str(root/'analysis/shots'),sound=False,
 debug_except='bus,address,illegal',extra_args=['--machine','st','--memsize','4','--monitor','rgb']) as h:
 h.wait(8)
 base=h.basepage()['text']
 def word(name):
  address=base+syms[name]; return h.mem(address,2).u16(address)
 frames=word('gChunkyDemoFrames'); assert frames>0
 print('frames:',frames,flush=True)
 print('animation:',h.screenshot(),flush=True)
 h.tap('SPACE'); assert h.mem(base+syms['sPaused'],1).u8(base+syms['sPaused'])==1
 x,y=word('sX'),word('sY'); h.wait(0.7)
 assert (word('sX'),word('sY'))==(x,y)
 print('paused:',h.screenshot(),flush=True)
 h.tap('SPACE'); assert h.mem(base+syms['sPaused'],1).u8(base+syms['sPaused'])==0
 h.wait(0.7); assert word('gChunkyDemoFrames')!=frames
 h.control('hatari-event keydown 01');h.wait(0.3);h.control('hatari-event keyup 01');h.wait(1)
 print('exit:',h.screenshot(),flush=True)
 (root/'analysis/hatari.log').write_text('\n'.join(h.lines))
 assert not any('Address Error' in l or 'Bus Error' in l or 'Exception' in l for l in h.lines)
print('PASS: ST animation, pause/resume and exit')
