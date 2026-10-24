from pathlib import Path
import sys,os,time,struct,tempfile,json
from PIL import Image
os.environ.setdefault('SDL_VIDEODRIVER','dummy');os.environ.setdefault('SDL_AUDIODRIVER','dummy')
sys.path.insert(0,str(Path.home()/'.agents/skills/hatari-debugging/scripts'))
from hatari_session import HatariSession,nm_symbols
APP=Path(__file__).resolve().parents[1]
DEBUG=Path(os.environ.get('BOBS_DEBUG','/tmp/BOBSDBG.PRG'))
TOS=Path(os.environ.get('TOS',str(Path.home()/'Atari/tos/TOS v1.62 (1990)(Atari Corp)(STE)(De).img')))
class Probe:
 def __init__(self,h):
  self.h=h;self.tmp=Path(tempfile.mkdtemp(prefix='dckbobs-check-'));self.sy=nm_symbols(os.environ.get('BOBS_SYMBOLS',str(DEBUG)),nm='m68k-atari-mintelf-nm');h.wait(2);self.base=h.basepage()['text']
  for _ in range(80):
   if self.val('gBobsReady')==1:break
   h.wait(.1)
  assert self.val('gBobsReady')==1,h.lines[-20:]
 def addr(self,n):return self.base+self.sy[n]
 def raw(self,addr,size):
  p=self.tmp/'state.bin';p.unlink(missing_ok=True);self.h.debug(f'savebin {p} ${addr:x} ${size:x}',settle=.025)
  for _ in range(100):
   if p.exists()and p.stat().st_size==size:return p.read_bytes()
   time.sleep(.005)
  raise RuntimeError(self.h.lines[-20:])
 def data(self,n,size):return self.raw(self.addr(n),size)
 def val(self,n,size=2):return int.from_bytes(self.data(n,size),'big')
 def put(self,n,v):self.write(n,v.to_bytes(2,'big'))
 def write(self,n,b):self.h.debug(f'w ${self.addr(n):x} '+' '.join(f'${v:x}'for v in b),settle=.012)
 def request(self,code=1):
  self.put('gBobsCompleted',0);self.put('gBobsRequest',code)
  for _ in range(100):
   if self.val('gBobsCompleted')==code:return
   self.h.wait(.02)
  raise RuntimeError(('request',code,self.h.lines[-20:]))
 def pages(self):return struct.unpack('>4I',self.data('gScreenClass',20)[4:20])
 def preview(self,ptr,name):
  im=Image.frombytes('P',(320,200),decode(self.raw(ptr,32000)));pal=struct.unpack('>16H',(APP/'assets/PALETTE.BIN').read_bytes());rgb=[((v>>s)&7)*255//7 for v in pal for s in (8,4,0)];im.putpalette(rgb+[0]*(768-len(rgb)));im.save(APP/name,bits=4)
def decode(raw):
 out=bytearray(64000)
 for y in range(200):
  for x in range(20):
   words=struct.unpack_from('>4H',raw,y*160+x*8)
   for bit in range(16):out[y*320+x*16+bit]=sum(((words[q]>>(15-bit))&1)<<q for q in range(4))
 return bytes(out)
SOURCE=decode((APP/'source/BALLS.PI1').read_bytes()[34:])
PATH_NAMES=['NOEUD','CERCLE','2CERCLES','DOUBLE45','CER-45','CER_45~1','GROS_CER','REBOND']
PATHS=[[(x*24//25,32+y*3//5)for x,y in struct.iter_unpack('>hh',(APP/'source/paths'/f'{name}.DAT').read_bytes())]for name in PATH_NAMES]
def positions(path,indices):return [PATHS[path][n]for n in indices]
def stamp(raw,coords,count):
 for i,(xx,yy)in enumerate(coords[:count]):
  assert 0<=xx<=288 and 32<=yy<=140
  for y in range(27):
   for x in range(32):
    colour=SOURCE[((i%3)*27+y)*320+x]
    if not colour:continue
    off=(yy+y)*160+((xx+x)//16)*8;mask=0x8000>>((xx+x)&15)
    for q in range(4):
     word=int.from_bytes(raw[off+2*q:off+2*q+2],'big');word=word|mask if colour&(1<<q)else word&(~mask&65535);raw[off+2*q:off+2*q+2]=word.to_bytes(2,'big')
