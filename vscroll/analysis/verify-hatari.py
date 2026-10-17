"""Check the vertical viewport, keyboard control, both bird pages and restore."""
import sys,subprocess,struct
from pathlib import Path
from PIL import Image
sys.path.insert(0,str(Path.home()/'.codex/skills/hatari-debugging/scripts'))
from hatari_session import HatariSession
root=Path(__file__).resolve().parents[1]
nm=subprocess.check_output(['m68k-atari-mintelf-nm',str(root/'analysis/VSCDBG.PRG')],text=True)
syms={p[2]:int(p[0],16) for line in nm.splitlines() if len(p:=line.split())==3}
data=(root/'TOWER.BIN').read_bytes();palette=struct.unpack_from('>16H',data)
colours=[tuple((((((v>>s)&7)<<1)|(((v>>s)>>3)&1))*17) for s in (8,4,0)) for v in palette]
indices=[]
for y in range(400):
 for x in range(320):
  p=struct.unpack_from('>4H',data,32+y*160+(x//16)*8)
  indices.append(sum(((p[i]>>(15-x%16))&1)<<i for i in range(4)))
with HatariSession(str(root/'VSCROLL.PRG'),machine='ste',screenshot_dir=str(root/'analysis/shots'),sound=False,tos=str(Path.home()/'Atari/tos/TOS v2.06 (1991)(Atari Corp)(Mega-STE)(UK).img'),
 debug_except='bus,address,illegal',extra_args=['--memsize','4','--monitor','rgb']) as h:
 h.wait(8);base=h.basepage()['text']
 def addr(n):return base+syms[n]
 def word(n):
  a=addr(n);return h.mem(a,2).u16(a)
 def setword(n,v):h.debug('w $%x %d %d'%(addr(n),v>>8,v&255))
 assert word('gVScrollReady')==1
 before=word('gVScrollY');h.wait(.4);assert word('gVScrollY')!=before
 h.tap('SPACE');assert word('gVScrollAuto')==0
 setword('gBirdVisible',0);setword('gVScrollY',0);h.tap('DOWN',hold=.2)
 assert 0<word('gVScrollY')<200
 setword('gVScrollY',200);h.tap('UP',hold=.2);assert 0<word('gVScrollY')<200
 for y in (() if '--sprite-only' in sys.argv else (0,1,7,8,15,16,31,32,199,200)):
  setword('gVScrollY',y)
  shot=Image.open(h.screenshot()).convert('RGB')
  for yy in range(200):
   for xx in range(320):
    assert shot.getpixel((96+xx*2,58+yy*2))==colours[indices[(y+yy)*320+xx]],(y,xx,yy)
  print('PASS vertical pixels Y=',y,flush=True)
 setword('gVScrollY',123);setword('gBirdMoving',0);setword('gBirdPhase',70);setword('gBirdVisible',1);h.wait(1)
 x=word('gBirdX');y=word('gBirdY');assert (x,y)==(86,233)
 background=data[32:]+bytes(32*160)
 expected=bytearray(background)
 shape=[0,0,0x8001,0xc003,0xe007,0x700e,0x381c,0x1c38,0x0ff0,0x07e0,0x03c0,0x0180,0,0,0,0]
 for yy in range(16):
  for xx in range(16):
   if shape[yy]&(1<<(15-xx)):
    wx=x+xx;wy=y+yy;offset=wy*160+(wx//16)*8;bit=0x8000>>(wx%16)
    for p in range(4):
     w=struct.unpack_from('>H',expected,offset+2*p)[0]
     struct.pack_into('>H',expected,offset+2*p,w|bit)
 a=addr('gScreenClass');mem=h.mem(a,20);pages=[mem.u32(a+4+i*4) for i in range(3)]
 for page in pages[:2]:
  actual=h.mem(page,69120).bytes(page,69120)
  if actual!=expected:
   differences=[(i,i//160,(i%160)//8*16,a,b) for i,(a,b) in enumerate(zip(actual,expected)) if a!=b]
   print('sprite mismatch',hex(page),'count',len(differences),'first',differences[:24],flush=True)
   (root/'analysis/actual.bin').write_bytes(actual);(root/'analysis/expected.bin').write_bytes(expected)
  assert actual==expected
 assert h.mem(pages[2],69120).bytes(pages[2],69120)==background
 print('PASS bird: both pages, transparency, clean background and 32-line reserve',flush=True)
 print('bird screenshot:',h.screenshot(),flush=True)
 setword('gBirdVisible',0);h.wait(1)
 for page in pages[:2]:assert h.mem(page,69120).bytes(page,69120)==background
 print('PASS complete sprite restore',flush=True)
 h.control('hatari-event keydown 01');h.wait(.3);h.control('hatari-event keyup 01');h.wait(1)
 print('exit screenshot:',h.screenshot(),flush=True)
 (root/'analysis/hatari.log').write_text('\n'.join(h.lines))
 assert not any('Address Error' in l or 'Bus Error' in l or 'Exception' in l for l in h.lines)
print('PASS: auto/manual vertical scrolling, all pixels, sprite pages, restore and exit')
