"""All masks, inverse sectors, both pages and CPU/blitter native copy paths."""
import os,sys,struct,time,json,hashlib
from pathlib import Path
from PIL import Image
os.environ.setdefault('SDL_VIDEODRIVER','dummy');os.environ.setdefault('SDL_AUDIODRIVER','dummy')
sys.path.insert(0,str(Path.home()/'.agents/skills/hatari-debugging/scripts'))
from hatari_session import HatariSession,nm_symbols
root=Path(__file__).resolve().parents[1];out=root/'analysis';sym=nm_symbols(str(out/'WEDGESDBG.PRG'),nm='m68k-atari-mintelf-nm')
frames=(root/'assets/FRAMES.BIN').read_bytes();results=[]
for machine in ('ste','st'):
 tos='TOS v1.62 (1990)(Atari Corp)(STE)(De).img'if machine=='ste'else 'TOS v2.06 (1991)(Atari Corp)(Mega-STE)(UK).img'
 with HatariSession(str(root/'WEDGES.PRG'),tos=str(Path.home()/'Atari/tos'/tos),machine=machine,sound=False,screenshot_dir=str(out/'shots'),debug_except='bus,address,illegal',extra_args=['--confirm-quit','false','--memsize','1','--cpuclock','8','--monitor','rgb'])as h:
  h.wait(9);base=h.basepage()['text'];a=lambda n:base+sym[n]
  def step():h.stdin_cmd('b pc = $%x :once'%a('Wedges_FrameDone'),settle=.003);h.stdin_cmd('c',settle=.04)
  def dump(addr,n):
   f=out/'dump.bin';f.unlink(missing_ok=True);h.stdin_cmd('savebin %s $%x $%x'%(f,addr,n),settle=.005)
   for _ in range(200):
    if f.exists()and f.stat().st_size==n:break
    time.sleep(.005)
   data=f.read_bytes();assert len(data)==n;return data
  def u16(n):return struct.unpack('>H',dump(a(n),2))[0]
  def write(n,v):h.stdin_cmd('w $%x $%02x $%02x'%(a(n),(v>>8)&255,v&255),settle=.004)
  def key(k):h.control('hatari-event keydown '+k,settle=.01);step();h.control('hatari-event keyup '+k,settle=.01);step()
  h.debug('b pc = $%x :once'%a('Wedges_FrameDone'),settle=.2);assert u16('gWedgesReady')==1
  cache=struct.unpack('>I',dump(a('gWedgesCache'),4))[0];assert cache
  assert dump(cache,256000)==frames,'startup cache differs from original SuperHex oracle'
  build_vbl=struct.unpack('>I',dump(a('gWedgesBuildVbl'),4))[0]
  assert u16('gWedgesHasBlitter')==(machine=='ste')
  key('25');assert u16('gWedgesPause')==1
  first=struct.unpack('>I',dump(a('gWedgesScreen'),4))[0];background=bytearray(dump(first,32000))
  for pos in range(6,32000,8):background[pos:pos+2]=b'\0\0'
  assert all(background[pos:pos+2]==b'\0\0'for pos in range(0,32000,8))
  assert all(background[pos:pos+2]==b'\0\0'for pos in range(6,32000,8))
  for backend in ([1,0]if machine=='ste'else [0]):
   write('gWedgesBlitter',backend);pages=set();count=0
   for inverse in (0,1):
    for frame in range(32):
     angle=inverse*256+frame*8;write('gWedgesAngle',angle)
     mask=frames[frame*8000:(frame+1)*8000];wanted=bytearray(background)
     for w in range(4000):
      word=int.from_bytes(mask[w*2:w*2+2],'big')^(65535 if inverse else 0)
      struct.pack_into('>H',wanted,w*8+4,word)
     for _ in range(2):
      step();screen=struct.unpack('>I',dump(a('gWedgesScreen'),4))[0];actual=dump(screen,32000)
      assert u16('gWedgesDrawAngle')==angle
      if actual!=wanted:
       (out/'actual.bin').write_bytes(actual);(out/'expected.bin').write_bytes(wanted)
       raise AssertionError((machine,backend,inverse,frame,next((i,x,y)for i,(x,y)in enumerate(zip(actual,wanted))if x!=y)))
      pages.add(screen);count+=1
     if machine=='ste'and backend==1 and inverse==0 and frame==9:
      palette=struct.unpack('>16H',dump(0xffff8240,32));rgb=[tuple(((((v>>s)&7)<<1)|(((v>>s)>>3)&1))*17 for s in(8,4,0))for v in palette];pixels=[]
      for y in range(200):
       for w in range(20):
        planes=struct.unpack_from('>4H',actual,y*160+w*8)
        pixels.extend(rgb[sum(((v>>(15-i))&1)<<p for p,v in enumerate(planes))]for i in range(16))
      im=Image.new('RGB',(320,200));im.putdata(pixels);im.resize((640,400),Image.Resampling.NEAREST).save(out/'preview.png')
   assert len(pages)==2
   results.append({'machine':machine,'TOS':tos,'startup_cache_bytes_verified':256000,'startup_generation_vbl':build_vbl,'backend':'blitter'if backend else 'CPU','full_frame_comparisons':count,'phases':32,'parities':2,'pages':2})
   print('PASS',results[-1],flush=True)
  # Genuine keyboard controls: reverse/speed, B toggle where supported, resume.
  old=u16('gWedgesDirection');key('19');assert u16('gWedgesDirection')==((-old)&65535)
  speed=u16('gWedgesSpeed');key('72');assert u16('gWedgesSpeed')==speed+1
  key('80');assert u16('gWedgesSpeed')==speed
  if machine=='ste':old=u16('gWedgesBlitter');key('48');assert u16('gWedgesBlitter')==1-old
  angle=u16('gWedgesAngle');key('57');assert u16('gWedgesPause')==0
  step();assert u16('gWedgesAngle')!=angle
  h.stdin_cmd('c',settle=.05);h.tap('ESC',hold=.13,after=.5)
  assert h.mem(a('gWedgesExited'),2).u16(a('gWedgesExited'))==1
  assert not any(any(s in l for s in ['Bus Error','Address Error','Illegal instruction'])for l in h.lines)
(out/'verification.json').write_text(json.dumps({'program_sha256':hashlib.sha256((root/'WEDGES.PRG').read_bytes()).hexdigest(),'configuration':'68000, 8 MHz, 1 MiB, PAL RGB','checks':'Startup RAM cache compared byte-for-byte with original SuperHex oracle. All 32 phases, both inverse parities, both screen pages, preserved other planes; STE blitter+CPU and plain ST CPU; pause/reverse/speed/backend keyboard controls and clean exit. See tables-verification.json for exact original SuperHex geometry equivalence.','results':results},indent=2)+'\n')
(out/'dump.bin').unlink(missing_ok=True);print('PASS all native wedges tests',flush=True)
