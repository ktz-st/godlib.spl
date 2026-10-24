from pathlib import Path
import sys,os,time,json,struct,tempfile,hashlib
from PIL import Image
os.environ.setdefault('SDL_VIDEODRIVER','dummy');os.environ.setdefault('SDL_AUDIODRIVER','dummy')
sys.path.insert(0,str(Path.home()/'.agents/skills/hatari-debugging/scripts'))
from hatari_session import HatariSession,nm_symbols
APP=Path(__file__).resolve().parents[1];DEBUG=Path(os.environ.get('DR_DEBUG','/tmp/DRDBG.PRG'));TOS=Path(os.environ.get('TOS',str(Path.home()/'Atari/tos/TOS v1.62 (1990)(Atari Corp)(STE)(De).img')))
META=json.loads((APP/'assets/source.json').read_text());PAL=(APP/'assets/PALETTE.BIN').read_bytes();ATLAS=Image.open(APP/'source/BIG.png')
class Probe:
 def __init__(self,h):
  self.h=h;self.tmp=Path(tempfile.mkdtemp(prefix='dckroute-'));self.sy=nm_symbols(os.environ.get('DR_SYMBOLS',str(DEBUG)),nm='m68k-atari-mintelf-nm');h.wait(2);self.base=h.basepage()['text']
  for _ in range(100):
   if self.val('gRouteReady')==1:break
   h.wait(.1)
  assert self.val('gRouteReady')==1,h.lines[-20:]
 def addr(self,n):return self.base+self.sy[n]
 def raw(self,addr,size):
  f=self.tmp/'mem.bin';f.unlink(missing_ok=True);self.h.debug(f'savebin {f} ${addr:x} ${size:x}',settle=.018)
  for _ in range(100):
   if f.exists()and f.stat().st_size==size:return f.read_bytes()
   time.sleep(.003)
  raise RuntimeError(self.h.lines[-20:])
 def data(self,n,size):return self.raw(self.addr(n),size)
 def val(self,n,size=2):return int.from_bytes(self.data(n,size),'big')
 def put(self,n,v):self.write(self.addr(n),v.to_bytes(2,'big'))
 def write(self,addr,b):self.h.debug(f'w ${addr:x} '+' '.join('$%x'%x for x in b),settle=.01)
 def request(self,n=1):
  self.put('gRouteCompleted',0);self.put('gRouteBenchRequest',n)
  for _ in range(100):
   if self.val('gRouteCompleted')==n:return
   self.h.wait(.02)
  raise RuntimeError(('request',n,self.h.lines[-20:]))
 def state(self):
  return dict(mode=self.val('gRouteMode'),profile=self.val('gRouteProfile'),phase=self.val('gRoutePhase'),queue=list(struct.unpack('>9H',self.data('gRouteQueue',18))),y=list(struct.unpack('>40H',self.data('gRouteY',80))))
 def expected(self,state):
  # Independent oracle reads indexed atlas pixels, never the packed font/pointers.
  idx=bytearray(64000);mode=state['mode'];phase=state['phase'];queue=state['queue']
  if mode==2:
   for y in range(160):
    pos=y+phase;g=queue[pos//40];row=pos%40
    if row<32 and g<48:
     for x in range(40):idx[(y+24)*320+144+x]=ATLAS.getpixel((g%8*40+x,g//8*32+row))
  else:
   for x in range(320):
    pos=x+phase;g=queue[pos//40];col=pos%40;y0=state['y'][x//8]
    if g<48:
     for y in range(32):idx[(y0+y)*320+x]=ATLAS.getpixel((g%8*40+col,g//8*32+y))
  planar=bytearray(32000)
  for y in range(24,184):
   for group in range(20):
    values=idx[y*320+group*16:y*320+group*16+16]
    for q in range(4):struct.pack_into('>H',planar,y*160+group*8+q*2,sum(((v>>q)&1)<<(15-bit)for bit,v in enumerate(values)))
  return bytes(planar)
 def check(self):
  s=self.state();actual=self.raw(self.val('gRouteScreen',4),32000);want=self.expected(s)
  if actual!=want:
   off=next(i for i in range(32000)if actual[i]!=want[i]);raise AssertionError((s,'offset',off,'got',actual[off:off+16].hex(),'want',want[off:off+16].hex()))
  return s
 def preview(self,ptr,name):
  native=self.raw(ptr,32000);idx=bytearray(64000)
  for y in range(200):
   for group in range(20):
    words=struct.unpack_from('>4H',native,y*160+group*8)
    for bit in range(16):idx[y*320+group*16+bit]=sum(((words[q]>>(15-bit))&1)<<q for q in range(4))
  pal=struct.unpack('>16H',PAL);rgb=[(((((word>>s)&7)<<1)|((word>>(s+3))&1))*17)for word in pal for s in(8,4,0)]
  im=Image.frombytes('P',(320,200),bytes(idx));im.putpalette(rgb+[0]*(768-len(rgb)));im.save(APP/name,bits=4)
 def exit(self):
  self.h.control('hatari-event keydown 01');self.h.wait(.15);self.h.control('hatari-event keyup 01');self.h.wait(.2);assert self.val('gRouteExited')==1
