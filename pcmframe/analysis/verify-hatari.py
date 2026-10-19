import os,sys,json,subprocess
from pathlib import Path
sys.path.insert(0,str(Path.home()/'.codex/skills/hatari-debugging/scripts'))
from hatari_session import HatariSession
root=Path(__file__).resolve().parents[1]
nm=subprocess.check_output(['m68k-atari-mintelf-nm','-n',str(root/'analysis/PCMFRDBG.PRG')],text=True)
syms={l.split()[2]:int(l.split()[0],16) for l in nm.splitlines() if len(l.split())==3}
with HatariSession(str(root/'PCMFRAME.PRG'),screenshot_dir=str(root/'analysis/shots'),sound=False,tos=os.environ.get('HATARI_TOS'),debug_except='bus,address,illegal',extra_args=['--confirm-quit','false','--memsize','4','--monitor','rgb']) as h:
 h.wait(7);base=h.basepage();a=lambda n:base['text']+syms[n]
 slab=a('gPcmFrameMixerState')
 def state(tag):
  m=h.mem(slab,80);r=[m.bytes(slab+x,1)[0]!=0 for x in [0x42,0x41,0x3f]]
  print(tag,r,flush=True);return r
 assert not any(state('startup'))
 h.tap('F9');assert h.mem(a('sRasterDebug'),1).bytes(a('sRasterDebug'),1)[0]==1
 h.tap('F4');assert all(state('three channels'))
 print('raster shot',h.screenshot(),flush=True)
 assert h.mem(0xffff8240,2).u16(0xffff8240)==0
 h.wait(2.1);assert not any(state('one-shots finished'))
 h.tap('F5');h.wait(2.1);assert state('channel 2 loop')==[False,True,False]
 h.tap('F6');assert not any(state('stop'))
 h.tap('F9');assert h.mem(a('sRasterDebug'),1).bytes(a('sRasterDebug'),1)[0]==0
 h.control('hatari-event keydown 01');h.wait(.1);h.control('hatari-event keyup 01');h.wait(1);print('desktop shot',h.screenshot(),flush=True)
 (root/'analysis/hatari-raster.log').write_text('\n'.join(h.lines))
 assert not any('ERROR' in l or 'Exception' in l or 'Address Error' in l or 'Bus Error' in l for l in h.lines)
print('PASS PCM Frame: three channels, loop, stop, raster on/off, palette restore and ESC',flush=True)
