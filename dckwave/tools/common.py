from pathlib import Path
import sys,os,time,json,struct,tempfile,hashlib
from PIL import Image
os.environ.setdefault('SDL_VIDEODRIVER','dummy');os.environ.setdefault('SDL_AUDIODRIVER','dummy')
sys.path.insert(0,str(Path.home()/'.agents/skills/hatari-debugging/scripts'))
from hatari_session import HatariSession,nm_symbols
APP=Path(__file__).resolve().parents[1];DEBUG=Path(os.environ.get('DW_DEBUG','/tmp/DWDBG.PRG'));TOS=Path(os.environ.get('TOS',str(Path.home()/'Atari/tos/TOS v1.62 (1990)(Atari Corp)(STE)(De).img')))
META=json.loads((APP/'assets/source.json').read_text());SHIFTS=META['shifts'];MASKS=[15,2,5];NAMES=['all','one','two']
PICTURE=(APP/'assets/PICTURE.BIN').read_bytes();PALETTE=(APP/'assets/PALETTE.BIN').read_bytes()
class Probe:
 def __init__(self,h):
  self.h=h;self.tmp=Path(tempfile.mkdtemp(prefix='dckwave-'));self.sy=nm_symbols(os.environ.get('DW_SYMBOLS',str(DEBUG)),nm='m68k-atari-mintelf-nm');h.wait(2);self.base=h.basepage()['text']
  for _ in range(100):
   if self.val('gDwReady')==1:break
   h.wait(.1)
  assert self.val('gDwReady')==1,h.lines[-20:]
 def addr(self,n):return self.base+self.sy[n]
 def raw(self,addr,size):
  f=self.tmp/'mem.bin';f.unlink(missing_ok=True);self.h.debug(f'savebin {f} ${addr:x} ${size:x}',settle=.025)
  for _ in range(100):
   if f.exists()and f.stat().st_size==size:return f.read_bytes()
   time.sleep(.005)
  raise RuntimeError(self.h.lines[-20:])
 def data(self,n,size):return self.raw(self.addr(n),size)
 def val(self,n,size=2):return int.from_bytes(self.data(n,size),'big')
 def put(self,n,v):self.h.debug(f'w ${self.addr(n):x} ${(v>>8)&255:x} ${v&255:x}',settle=.012)
 def request(self,n=1):
  self.put('gDwCompleted',0);self.put('gDwRequest',n)
  for _ in range(100):
   if self.val('gDwCompleted')==n:return
   self.h.wait(.02)
  raise RuntimeError(('request',n,self.h.lines[-20:]))
 def pages(self):return struct.unpack('>4I',self.data('gScreenClass',20)[4:20])
 def waitval(self,name,value):
  for _ in range(100):
   if self.val(name)==value:return
   self.h.wait(.02)
  raise RuntimeError((name,value,self.val(name),self.h.lines[-20:]))
 def preview(self,ptr,name):
  native=self.raw(ptr,32000);idx=bytearray(64000)
  for y in range(200):
   for group in range(20):
    words=struct.unpack_from('>4H',native,y*160+group*8)
    for bit in range(16):idx[y*320+group*16+bit]=sum(((words[q]>>(15-bit))&1)<<q for q in range(4))
  pal=struct.unpack('>16H',PALETTE);rgb=[(((((word>>s)&7)<<1)|((word>>(s+3))&1))*17)for word in pal for s in (8,4,0)]
  im=Image.frombytes('P',(320,200),bytes(idx));im.putpalette(rgb+[0]*(768-len(rgb)));im.save(APP/name,bits=4)

# Independent reference: shift complete 320-bit rows, not word carry chains.
ROWS=[[int.from_bytes(b''.join(PICTURE[y*160+x*8+p*2:y*160+x*8+p*2+2] for x in range(20)), 'big') for p in range(4)] for y in range(160)]
def expected(back,mask,phase):
 out=bytearray(back)
 for y in range(160):
  for p in range(4):
   shift=SHIFTS[(phase+y*2)&255] if mask&(1<<p) else 0
   value=ROWS[y][p]>>shift if shift>=0 else (ROWS[y][p]<<-shift)&((1<<320)-1)
   words=value.to_bytes(40,'big')
   for x in range(20):out[(y+24)*160+x*8+p*2:(y+24)*160+x*8+p*2+2]=words[x*2:x*2+2]
 return out
