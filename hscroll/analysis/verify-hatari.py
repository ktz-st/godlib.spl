"""Verify fine/coarse STE scroll against an independent pixel reference."""
import sys,subprocess,struct
from pathlib import Path
from PIL import Image
sys.path.insert(0,str(Path.home()/'.codex/skills/hatari-debugging/scripts'))
from hatari_session import HatariSession
root=Path(__file__).resolve().parents[1]
nm=subprocess.check_output(['m68k-atari-mintelf-nm',str(root/'analysis/HSCRDBG.PRG')],text=True)
syms={p[2]:int(p[0],16) for line in nm.splitlines() if len(p:=line.split())==3}
with HatariSession(str(root/'analysis/HSCRDBG.PRG'),machine='ste',screenshot_dir=str(root/'analysis/shots'),sound=False,
 debug_except='bus,address,illegal',extra_args=['--memsize','4','--monitor','rgb']) as h:
 h.wait(20);base=h.basepage()['text']
 def addr(n):return base+syms[n]
 def word(n):
  a=addr(n);return h.mem(a,2).u16(a)
 assert word('gSpriteStrideResult')==0
 assert word('gHScrollReady')==1
 h.tap('SPACE');assert word('gHScrollAuto')==0
 palette=[0,0x777,0x700,0x070,0x007,0x770,0x707,0x077,0x333,0x555,0x733,0x373,0x337,0x773,0x737,0x555]
 colours=[tuple(((v>>s)&7)*34 for s in (8,4,0)) for v in palette]
 def setword(n,v): h.debug('w $%x %d %d'%(addr(n),v>>8,v&255))
 origin=None
 for x,y in ((0,0),(1,0),(15,0),(16,0),(17,0),(31,0),(32,0),(319,0),(320,0),(15,1),(16,31),(320,32)):
  setword('gHScrollX',x);setword('gHScrollY',y)
  regs=h.mem(0xffff820f,1).u8(0xffff820f)
  fine=h.mem(0xffff8265,1).u8(0xffff8265)&15
  assert fine==x%16,(x,y,fine)
  assert regs==80-(4 if fine else 0),(x,y,regs)
  shot=Image.open(h.screenshot()).convert('RGB')
  if origin is None:
   # First pattern line is white from edge to edge; locate the active screen.
   for yy in range(30,100):
    if all(shot.getpixel((xx,yy))==colours[1] for xx in range(96,736)):
     origin=(96,yy);break
   assert origin is not None
  ox,oy=origin
  for yy in range(200):
   for xx in range(320):
    wx,wy=x+xx,y+yy
    index=1 if (wx&15)==0 or (wy&15)==0 else 2+((wx>>4)+((wy%32)>>4))%14
    assert shot.getpixel((ox+xx*2,oy+yy*2))==colours[index],(x,y,xx,yy,index,shot.getpixel((ox+xx*2,oy+yy*2)))
  print('PASS pixels/stride/fine X,Y=',x,y,flush=True)
 h.control('hatari-event keydown 01');h.wait(.3);h.control('hatari-event keyup 01');h.wait(1)
 print('exit',h.screenshot(),flush=True)
 (root/'analysis/hatari.log').write_text('\n'.join(h.lines))
 assert not any('Address Error' in l or 'Bus Error' in l or 'Exception' in l for l in h.lines)
print('PASS: wide sprite reference tests, horizontal/vertical viewport, fine/coarse boundaries, exit')
