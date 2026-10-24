from pathlib import Path
import sys,os,time,json,struct,tempfile,hashlib
from PIL import Image
os.environ.setdefault('SDL_VIDEODRIVER','dummy');os.environ.setdefault('SDL_AUDIODRIVER','dummy')
sys.path.insert(0,str(Path.home()/'.agents/skills/hatari-debugging/scripts'))
from hatari_session import HatariSession,nm_symbols
APP=Path(__file__).resolve().parents[1];DEBUG=Path(os.environ.get('DB_DEBUG','/tmp/DBDBG.PRG'));TOS=Path(os.environ.get('TOS',str(Path.home()/'Atari/tos/TOS v1.62 (1990)(Atari Corp)(STE)(De).img')))
META=json.loads((APP/'assets/source.json').read_text());PICTURE=(APP/'assets/PICTURE.BIN').read_bytes();PALETTE=(APP/'assets/PALETTE.BIN').read_bytes();MASKS=META['masks'];NAMES=META['modes']
class Probe:
 def __init__(self,h):
  self.h=h;self.tmp=Path(tempfile.mkdtemp(prefix='dckblock-'));self.sy=nm_symbols(os.environ.get('DB_SYMBOLS',str(DEBUG)),nm='m68k-atari-mintelf-nm');h.wait(2);self.base=h.basepage()['text']
  for _ in range(100):
   if self.val('gDbReady')==1:break
   h.wait(.1)
  assert self.val('gDbReady')==1,h.lines[-20:]
 def addr(self,n):return self.base+self.sy[n]
 def raw(self,addr,size):
  f=self.tmp/'mem.bin';f.unlink(missing_ok=True);self.h.debug(f'savebin {f} ${addr:x} ${size:x}',settle=.015)
  for _ in range(100):
   if f.exists()and f.stat().st_size==size:return f.read_bytes()
   time.sleep(.003)
  raise RuntimeError(self.h.lines[-20:])
 def data(self,n,size):return self.raw(self.addr(n),size)
 def val(self,n,size=2):return int.from_bytes(self.data(n,size),'big')
 def write(self,addr,b):self.h.debug(f'w ${addr:x} '+' '.join('$%x'%x for x in b),settle=.008)
 def put(self,n,v):self.write(self.addr(n),v.to_bytes(2,'big'))
 def request(self,n=1):
  self.put('gDbCompleted',0);self.put('gDbRequest',n)
  for _ in range(100):
   if self.val('gDbCompleted')==n:return
   self.h.wait(.02)
  raise RuntimeError(('request',n,self.h.lines[-20:]))
 def pages(self):return struct.unpack('>4I',self.data('gScreenClass',20)[4:20])
 def key(self,scan):
  self.h.control(f'hatari-event keydown {scan:02d}');self.h.wait(.055);self.h.control(f'hatari-event keyup {scan:02d}');self.h.wait(.08)
 def preview(self,ptr,name):
  native=self.raw(ptr,32000);idx=bytearray(64000)
  for y in range(200):
   for group in range(20):
    words=struct.unpack_from('>4H',native,y*160+group*8)
    for bit in range(16):idx[y*320+group*16+bit]=sum(((words[q]>>(15-bit))&1)<<q for q in range(4))
  pal=struct.unpack('>16H',PALETTE);rgb=[(((((word>>s)&7)<<1)|((word>>(s+3))&1))*17)for word in pal for s in(8,4,0)]
  im=Image.frombytes('P',(320,200),bytes(idx));im.putpalette(rgb+[0]*(768-len(rgb)));im.save(APP/name,bits=4)
 def exit(self):
  self.h.control('hatari-event keydown 01');self.h.wait(.12);self.h.control('hatari-event keyup 01');self.h.wait(.2);assert self.val('gDbExited')==1

def expected(back,mode,mask,phase):
 # Recompose directly from the immutable picture, without reading the ASM
 # command list, row kernels or page history. Each mapping describes pixels.
 stage=bytearray(PICTURE)
 def copy(dx,dy,sx,sy,width):
  src=sy*160+sx//2;dst=dy*160+dx//2;size=width//2
  if mask==15:stage[dst:dst+size]=PICTURE[src:src+size]
  else:
   for plane in range(4):
    if mask&(1<<plane):
     for byte in(0,1):
      p=plane*2+byte;stage[dst+p:dst+size+p:8]=PICTURE[src+p:src+size+p:8]
 if mode==0:
  x,y=META['positions'][phase]
  for row in range(64):copy(x,y+row,96,24+row,128)
 elif mode==1:
  for y in range(160):copy(0,y,0,(y//16*16+phase)%160,320)
 elif mode==2:
  q=phase if phase<80 else 159-phase
  for y in range(160):
   sy=[q+2*y,79-q+2*(y-40),159-q-2*(y-80),80+q-2*(y-120)][y//40]
   copy(0,y,0,sy,320)
 elif mode==3:
  for y in range(160):copy(0,y,0,(159-phase-y)%160,320)
 elif mode==4:
  for col in range(10):
   for y in range(40,120):copy(col*32,y,((col+phase//16)%10)*32,159-y if col&1 else y,32)
 else:raise ValueError(mode)
 out=bytearray(back);out[24*160:184*160]=stage;return bytes(out)
