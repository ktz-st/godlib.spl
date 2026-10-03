"""Compare scrolling panorama pixels, then verify both sprite buffers and restore."""
import sys,subprocess,struct
from pathlib import Path
from PIL import Image
sys.path.insert(0,str(Path.home()/'.codex/skills/hatari-debugging/scripts'))
from hatari_session import HatariSession
root=Path(__file__).resolve().parents[1]
nm=subprocess.check_output(['m68k-atari-mintelf-nm',str(root/'analysis/PANDBG.PRG')],text=True)
syms={p[2]:int(p[0],16) for line in nm.splitlines() if len(p:=line.split())==3}
data=(root/'PANORAMA.BIN').read_bytes();palette=struct.unpack_from('>16H',data)
colours=[tuple(((v>>s)&7)*34 for s in (8,4,0)) for v in palette]
def pixel(x,y):
 p=struct.unpack_from('>4H',data,32+y*320+(x//16)*8)
 return sum(((p[i]>>(15-x%16))&1)<<i for i in range(4))
with HatariSession(str(root/'HSCROLL.PRG'),machine='ste',screenshot_dir=str(root/'analysis/panorama-shots'),sound=False,
 debug_except='bus,address,illegal',extra_args=['--memsize','4','--monitor','rgb']) as h:
 h.wait(20);base=h.basepage()['text']
 def addr(n):return base+syms[n]
 def word(n):
  a=addr(n);return h.mem(a,2).u16(a)
 def setword(n,v): h.debug('w $%x %d %d'%(addr(n),v>>8,v&255))
 assert word('gHScrollReady')==1 and word('gSpriteStrideResult')==0
 h.tap('SPACE');assert word('gHScrollAuto')==0
 setword('gBirdVisible',0)
 for x in (0,1,15,16,17,31,32,319,320):
  setword('gHScrollX',x)
  shot=Image.open(h.screenshot()).convert('RGB')
  for yy in range(200):
   for xx in range(320):
    assert shot.getpixel((96+xx*2,58+yy*2))==colours[pixel(x+xx,yy)],(x,xx,yy)
  print('PASS panorama X=',x,flush=True)
 setword('gHScrollX',123);setword('gBirdMoving',0);setword('gBirdPhase',70);setword('gBirdVisible',1)
 h.wait(1)
 x=word('gBirdX');y=word('gBirdY');assert x==193 and y==110
 shape=[0,0,0x8001,0xc003,0xe007,0x700e,0x381c,0x1c38,0x0ff0,0x07e0,0x03c0,0x0180,0,0,0,0]
 # Three pages are allocated consecutively with rounded 256-byte page size.
 a=addr('gScreenClass');mem=h.mem(a,20);pages=[mem.u32(a+4+i*4) for i in range(3)]
 for page in pages[:2]:
  live=h.mem(page,64000).bytes(page,64000)
  for yy in range(200):
   for xx in range(640):
    planes=struct.unpack_from('>4H',live,yy*320+(xx//16)*8)
    actual=sum(((planes[i]>>(15-xx%16))&1)<<i for i in range(4))
    bird=x<=xx<x+16 and y<=yy<y+16 and shape[yy-y]&(1<<(15-(xx-x)))
    assert actual==(15 if bird else pixel(xx,yy)),(page,xx,yy,actual)
 print('PASS: both sprite pages, transparency and clean restored background',flush=True)
 print('bird screenshot:',h.screenshot(),flush=True)
 setword('gBirdVisible',0);h.wait(1)
 for page in pages[:2]: assert h.mem(page,64000).bytes(page,64000)==data[32:]
 print('PASS: complete background restored after hiding sprite',flush=True)
 h.control('hatari-event keydown 01');h.wait(.3);h.control('hatari-event keyup 01');h.wait(1)
 assert not any('Address Error' in l or 'Bus Error' in l or 'Exception' in l for l in h.lines)
print('PASS panorama, sprite, restore and exit')
