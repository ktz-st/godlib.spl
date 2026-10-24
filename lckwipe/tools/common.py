from pathlib import Path
import sys,os,time,json,struct,tempfile,hashlib
from PIL import Image
os.environ.setdefault('SDL_VIDEODRIVER','dummy');os.environ.setdefault('SDL_AUDIODRIVER','dummy')
sys.path.insert(0,str(Path.home()/'.agents/skills/hatari-debugging/scripts'))
from hatari_session import HatariSession,nm_symbols
APP=Path(__file__).resolve().parents[1];DEBUG=Path(os.environ.get('LW_DEBUG','/tmp/LWDBG.PRG'));TOS=Path(os.environ.get('TOS',str(Path.home()/'Atari/tos/TOS v1.62 (1990)(Atari Corp)(STE)(De).img')))
GEO=json.loads((APP/'assets/geometry.json').read_text());LIMITS=GEO['limits'];SPEEDS=GEO['speeds'];NAMES=['spiral','fold','lines','snake','instant','colours','centre','smear','interrows','curtaincols','intercols']
PICTURES=[(APP/f'assets/IMAGE{i}.BIN').read_bytes()for i in range(2)]
PALETTES=[(APP/f'assets/PALETTE{i}.BIN').read_bytes()for i in range(2)]
class Probe:
 def __init__(self,h):
  self.h=h;self.tmp=Path(tempfile.mkdtemp(prefix='lckwipe-'));self.sy=nm_symbols(os.environ.get('LW_SYMBOLS',str(DEBUG)),nm='m68k-atari-mintelf-nm');h.wait(2);self.base=h.basepage()['text']
  for _ in range(100):
   if self.val('gLwReady')==1:break
   h.wait(.1)
  assert self.val('gLwReady')==1,h.lines[-20:]
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
  self.put('gLwCompleted',0);self.put('gLwRequest',n)
  for _ in range(100):
   if self.val('gLwCompleted')==n:return
   self.h.wait(.02)
  raise RuntimeError(('request',n,self.h.lines[-20:]))
 def pages(self):return struct.unpack('>4I',self.data('gScreenClass',20)[4:20])
 def waitval(self,name,value):
  for _ in range(100):
   if self.val(name)==value:return
   self.h.wait(.02)
  raise RuntimeError((name,value,self.val(name),self.h.lines[-20:]))
 def preview(self,ptr,image,name,palette=None):
  native=self.raw(ptr,32000);idx=bytearray(64000)
  for y in range(200):
   for group in range(20):
    words=struct.unpack_from('>4H',native,y*160+group*8)
    for bit in range(16):idx[y*320+group*16+bit]=sum(((words[q]>>(15-bit))&1)<<q for q in range(4))
  pal=struct.unpack('>16H',PALETTES[image] if palette is None else palette);rgb=[(((((word>>s)&7)<<1)|((word>>(s+3))&1))*17)for word in pal for s in (8,4,0)]
  im=Image.frombytes('P',(320,200),bytes(idx));im.putpalette(rgb+[0]*(768-len(rgb)));im.save(APP/name,bits=4)
def expected(back,image,effect,closing,target):
 out=bytearray(back);src=PICTURES[image];work=bytearray(src if closing else bytes(25600))
 if effect in (0,3):
  for x,y in GEO['spiral'if effect==0 else'snake'][:target]:
   if effect==0:
    off=y*8*160+(x//2)*8+(x&1)
    for row in range(8):
     for q in range(4):i=off+row*160+q*2;work[i]=0 if closing else src[i]
   else:
    off=y*10*160+x*8
    for row in range(10):i=off+row*160;work[i:i+8]=bytes(8)if closing else src[i:i+8]
 elif effect==2:
  for y in range(160):
   start=y*160+(160-target*8 if y&1 else 0);end=start+target*8;work[start:end]=bytes(end-start)if closing else src[start:end]
 elif effect==1:
  n=160-target if closing else target
  # Independent equivalent of the adapted LCK fold's row-copy order.
  h=0 if not n else max(1,16-max(n-2,0)//10)
  work=bytearray(25600)
  for y in range(160):
   sy=y if y<n else min(159,n+2*h+14-(y-n))if n<=y<n+h else -1
   if sy>=0:work[y*160:(y+1)*160]=src[sy*160:(sy+1)*160]
 elif effect==4:
  if target:work=bytearray(25600) if closing else bytearray(src)
 elif effect==5:
  work=bytearray(src if (closing and target<8) or (not closing and target>0) else bytes(25600))
 elif effect in (6,8):
  order=([y for i in range(80) for y in ((i,159-i) if closing else (79-i,80+i))] if effect==6 else [y for i in range(0,160,2) for y in (i,159-i)])
  for y in order[:target]:work[y*160:(y+1)*160]=bytes(160) if closing else src[y*160:(y+1)*160]
 elif effect==7:
  n=target if closing else 160-target
  if (closing and target==160) or (not closing and target==0):work=bytearray(25600)
  else:
   work=bytearray(src)
   for y in range(n):work[y*160:(y+1)*160]=src[n*160:(n+1)*160]
 else:
  order=([x for i in range(160) for x in (i,319-i)] if effect==9 else [x for i in range(0,320,2) for x in (i,319-i)])
  covered=sum(1<<(319-x) for x in order[:target]);mask=(((1<<320)-1)^covered) if closing else covered
  for y in range(160):
   for plane in range(4):
    row=int.from_bytes(b''.join(src[y*160+x*8+plane*2:y*160+x*8+plane*2+2] for x in range(20)),'big')&mask
    words=row.to_bytes(40,'big')
    for x in range(20):work[y*160+x*8+plane*2:y*160+x*8+plane*2+2]=words[x*2:x*2+2]
 out[24*160:184*160]=work;return out

def expected_palette(image,effect,closing,target):
 if effect!=5:return PALETTES[image]
 count=8-target if closing else target
 words=struct.unpack('>16H',PALETTES[image])
 return struct.pack('>16H',*[word if i<count or i==15 else 0 for i,word in enumerate(words)])
def phase_calls(effect):return LIMITS[effect]*5+1 if effect==5 else (LIMITS[effect]+SPEEDS[effect]-1)//SPEEDS[effect]+1
def select(p,effect):
 current=p.val('gLwEffect')
 while current!=effect:
  forward=(effect-current)%len(NAMES)<=len(NAMES)//2
  p.h.tap('RIGHT' if forward else 'LEFT',hold=.025,after=.04)
  current=(current+(1 if forward else -1))%len(NAMES);p.waitval('gLwEffect',current)
