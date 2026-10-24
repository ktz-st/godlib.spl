from pathlib import Path
import sys,os,time,json,struct,tempfile,hashlib
from PIL import Image
os.environ.setdefault('SDL_VIDEODRIVER','dummy');os.environ.setdefault('SDL_AUDIODRIVER','dummy')
sys.path.insert(0,str(Path.home()/'.agents/skills/hatari-debugging/scripts'))
from hatari_session import HatariSession,nm_symbols
APP=Path(__file__).resolve().parents[1];DEBUG=Path(os.environ.get('WIPE_DEBUG','/tmp/WIPEDBG.PRG'));TOS=Path(os.environ.get('TOS',str(Path.home()/'Atari/tos/TOS v1.62 (1990)(Atari Corp)(STE)(De).img')))
import shutil,re
PICTURES=[(APP/name).read_bytes()[34:] for name in ['COAST.PI1','SPACE.PI1','FOREST.PI1']]
PALETTES=[(APP/name).read_bytes()[2:34] for name in ['COAST.PI1','SPACE.PI1','FOREST.PI1']]
SOURCE=(APP.parents[1]/'godlib/wipe/wipe_s.s').read_text(errors='replace')
MASKS=[]
for effect in range(1,40):
 part=SOURCE.split('gWipeData'+str(effect)+':',1)[1].split('gWipeData'+str(effect)+'_End:',1)[0];words=[]
 for line in part.splitlines():
  if re.match(r'\s*dc\.w',line,re.I):words += [int(v.strip().replace('$','0x'),0) for v in re.split(r'\s*dc\.w\s*',line,flags=re.I)[1].split(';')[0].split(',')]
 assert len(words)%16==0
 MASKS.append([words[i:i+16] for i in range(0,len(words),16)])
COUNTS=[len(m) for m in MASKS]
def staged(binary=DEBUG):
 folder=Path(tempfile.mkdtemp(prefix='wipe-boot-'));program=folder/Path(binary).name
 shutil.copy2(binary,program)
 for name in ['COAST.PI1','SPACE.PI1','FOREST.PI1']:shutil.copy2(APP/name,folder/name)
 return program
class Probe:
 def __init__(self,h):
  self.h=h;self.tmp=Path(tempfile.mkdtemp(prefix='wipe-'));self.sy=nm_symbols(os.environ.get('WIPE_SYMBOLS',str(DEBUG)),nm='m68k-atari-mintelf-nm');h.wait(2);self.base=h.basepage()['text']
  for _ in range(100):
   if self.val('gSlideReady')==1:break
   h.wait(.1)
  assert self.val('gSlideReady')==1,h.lines[-20:]
 def addr(self,n):return self.base+self.sy[n]
 def raw(self,addr,size,settle=.025):
  f=self.tmp/'mem.bin';f.unlink(missing_ok=True);self.h.debug(f'savebin {f} ${addr:x} ${size:x}',settle=settle)
  for _ in range(100):
   if f.exists()and f.stat().st_size==size:return f.read_bytes()
   time.sleep(.005)
  raise RuntimeError(self.h.lines[-20:])
 def data(self,n,size):return self.raw(self.addr(n),size)
 def val(self,n,size=2):return int.from_bytes(self.data(n,size),'big')
 def put(self,n,v):self.h.debug(f'w ${self.addr(n):x} ${(v>>8)&255:x} ${v&255:x}',settle=.012)
 def request(self,n=1):
  self.put('gWipeBenchDone',0);self.put('gWipeBenchRequest',n)
  for _ in range(100):
   if self.val('gWipeBenchDone')==n:return
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

SRCWORDS=struct.unpack('>16000H',PICTURES[0])
def reference(effect,frame,closing):
 mask=MASKS[effect][frame]
 if closing:
  acc=[0]*16
  for row in MASKS[effect][:frame+1]:acc=[a|b for a,b in zip(acc,row)]
  mask=[~v&65535 for v in acc]
 return b''.join(struct.pack('>80H',*[SRCWORDS[y*80+x]&mask[y&15] for x in range(80)]) for y in range(200))
def art_equal(actual,source):
 return all(actual[y*160:(y+1)*160]==source[y*160:(y+1)*160] for y in range(200) if not (8<=y<16 or 184<=y<200))
