"""ST smoke test: all three pictures, palette swaps, manual/automatic advance."""
import subprocess,sys,struct
from pathlib import Path
sys.path.insert(0,str(Path.home()/'.codex/skills/hatari-debugging/scripts'))
from hatari_session import HatariSession
root=Path(__file__).resolve().parents[1]
lines=subprocess.check_output(['m68k-atari-mintelf-nm','-n',str(root/'analysis/WIPEDBG.TOS')],text=True)
syms={p[2]:int(p[0],16) for line in lines.splitlines() if len(p:=line.split())==3}
with HatariSession(str(root/'WIPE.TOS'),screenshot_dir=str(root/'analysis/shots'),sound=False,
 debug_except='bus,address,illegal',extra_args=['--machine','st','--memsize','4','--monitor','rgb']) as h:
 h.wait(8)
 base=h.basepage()['text']
 def address(name): return base+syms[name]
 def state():
  start=address('gSlideReady'); m=h.mem(start,12)
  return {name:m.u16(address(name)) for name in ('gSlideReady','gAutoPause','gWipeTicks','gWipeStage','gWipeEffect','gSlideIndex')}
 def hold():
  for _ in range(8):
   s=state()
   if s['gWipeStage']==1: return s
   h.wait(0.3)
  raise AssertionError('wipe did not reach hold')
 assert state()['gSlideReady']==1
 h.tap('P'); assert state()['gAutoPause']==1
 first=hold(); visited=set()
 for _ in range(3):
  s=hold(); index=s['gSlideIndex']; visited.add(index)
  name=('COAST','SPACE','FOREST')[index]
  raw=(root/f'{name}.PI1').read_bytes()
  palette=h.mem(0xffff8240,32).bytes(0xffff8240,32)
  # Only 3 RGB bits per channel are defined on ST; unused readback bits float.
  assert tuple(v&0x777 for v in struct.unpack('>16H',palette))==struct.unpack('>16H',raw[2:34]),name+' palette'
  # Read the canonical planar buffer: it must equal the complete source.
  picture=h.mem(address('sTransition'),32000).bytes(address('sTransition'),32000)
  assert picture==raw[34:],name+' framebuffer'
  print(name,'effect',s['gWipeEffect']+1,'shot',h.screenshot(),flush=True)
  h.wait(0.3); assert hold()['gSlideIndex']==index  # auto pause holds the picture
  h.tap('SPACE'); s=hold(); assert s['gSlideIndex']==(index+1)%3
 assert visited=={0,1,2}
 h.tap('P'); assert state()['gAutoPause']==0
 previous=hold()['gSlideIndex']; h.wait(6)
 assert state()['gSlideIndex']!=previous
 h.control('hatari-event keydown 01');h.wait(0.3);h.control('hatari-event keyup 01');h.wait(1)
 print('exit',h.screenshot(),flush=True)
 (root/'analysis/hatari.log').write_text('\n'.join(h.lines))
 assert not any('Address Error' in l or 'Bus Error' in l or 'Exception' in l for l in h.lines)
print('PASS: three slides, individual palettes, complete frames, auto/manual advance, pause and exit')
