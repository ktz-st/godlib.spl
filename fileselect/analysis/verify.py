"""Release GEM selector: native mouse input, directory/filter and read-only IO."""
from pathlib import Path
import hashlib,json,os,struct,subprocess,sys,tempfile,time
from PIL import Image
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
sys.path.insert(0,str(Path.home()/'.agents/skills/hatari-debugging/scripts'))
from hatari_session import HatariSession,nm_symbols
r=Path(__file__).resolve().parents[1];out=r/'analysis'
sy=nm_symbols(str(out/'FSELDBG.PRG'),nm='m68k-atari-mintelf-nm')
binary=(r/'FILESEL.PRG').read_bytes();dbg=(out/'FSELDBG.PRG').read_bytes()
size=sum(struct.unpack_from('>2I',binary,2))
assert binary[28+128:28+size]==dbg[28+128:28+size]
fixtures={str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [r/'HELLO.TXT',r/'data/SECOND.TXT',r/'data/IGNORE.DAT']}
# macOS launcher shells may strip DYLD_INSERT_LIBRARIES. Use the native child.
hatari=os.environ.get('FSEL_HATARI','/opt/homebrew/opt/hatari/Hatari.app/Contents/MacOS/hatari')
with tempfile.TemporaryDirectory(prefix='godlib-fsel-')as tmp:
 tmp=Path(tmp);lib=tmp/'input.dylib';fifo=tmp/'input.pipe';os.mkfifo(fifo)
 flags=subprocess.check_output(['pkg-config','--cflags','--libs','sdl2'],text=True).split()
 subprocess.run(['clang','-dynamiclib',str(out/'sdl-input.c'),*flags,'-o',str(lib)],check=True)
 os.environ['FSEL_INPUT_PIPE']=str(fifo);os.environ['DYLD_INSERT_LIBRARIES']=str(lib)
 # Keep a local read end open too, so failed child injection cannot block Python.
 pipe=os.open(fifo,os.O_RDWR|os.O_NONBLOCK)
 try:
  with HatariSession(str(r/'FILESEL.PRG'),hatari=hatari,tos=str(Path.home()/'Atari/tos/TOS v1.62 (1990)(Atari Corp)(STE)(De).img'),screenshot_dir=str(out/'shots'),debug_except='bus,address,illegal',extra_args=['--confirm-quit','false','--memsize','1','--monitor','rgb','--cpuclock','8'])as h:
   h.wait(9);base=h.basepage()['text'];a=lambda name:base+sy[name]
   def dump(addr,count):
    p=out/'dump.bin';p.unlink(missing_ok=True)
    h.debug('savebin %s $%x $%x'%(p,addr,count),settle=.08)
    for _ in range(100):
     if p.exists()and p.stat().st_size==count:return p.read_bytes()
     time.sleep(.02)
    raise AssertionError(('dump timeout',h.lines[-12:]))
   def word(name):return struct.unpack('>H',dump(a(name),2))[0]
   def string(name):return dump(a(name),161 if name=='gPreview' else 512).split(b'\0')[0].decode('ascii')
   def move(dx,dy):
    os.write(pipe,('m %d %d\n'%(dx,dy)).encode());h.wait(.3)
   def point(x,y):
    # Two motions account for Hatari ignoring the first motion after reset.
    move(-2000,-2000);move(-2000,-2000);move(x*2,y*2)
   def click(x,y):
    point(x,y);h.control('hatari-event doubleclick');h.wait(.8)
   def snap(name):Image.open(h.screenshot()).save(out/(name+'.png'))
   def ready(calls,result):
    assert word('gSelectorReady')==1,(calls,h.lines[-12:])
    assert word('gSelectorCalls')==calls
    assert word('gSelectorResult')==result
   snap('dialog')
   # Cancel is a real GEM button click, not an injected return value.
   click(250,168);ready(1,0)
   assert string('gSelectedPath')==''
   h.tap('O');h.wait(.6)
   # Mouse double-click selects HELLO.TXT from the root listing.
   click(90,113);ready(2,1)
   assert string('gSelectedPath')=='C:\\HELLO.TXT',string('gSelectedPath')
   assert struct.unpack('>i',dump(a('gSelectedSize'),4))[0]==len((r/'HELLO.TXT').read_bytes())
   want=(r/'HELLO.TXT').read_bytes()
   assert string('gPreview')==''.join(chr(c)if 32<=c<=126 else'.'for c in want)
   snap('selected')
   h.tap('O');h.wait(.6)
   click(80,105) # DATA directory
   assert word('gSelectorReady')==0
   snap('directory-txt')
   # TXT filter hides IGNORE.DAT; SECOND.TXT is the first visible file.
   click(90,97);ready(3,1)
   assert string('gSelectedPath')=='C:\\DATA\\SECOND.TXT',string('gSelectedPath')
   assert string('gPreview')==''.join(chr(c)if 32<=c<=126 else'.'for c in (r/'data/SECOND.TXT').read_bytes())
   h.tap('A');h.wait(.6);snap('directory-all')
   click(90,97);ready(4,1) # IGNORE.DAT now appears first
   assert string('gSelectedPath')=='C:\\DATA\\IGNORE.DAT',string('gSelectedPath')
   h.tap('T');h.wait(.6);click(250,168);ready(5,0)
   h.tap('ESC');h.wait(.7)
   assert h.basepage()['text']!=base,'did not return to desktop'
   snap('desktop')
   assert not any('Bus Error'in line or'Address Error'in line or'CPU exception'in line for line in h.lines),h.lines[-20:]
 finally:os.close(pipe)
assert fixtures=={name:hashlib.sha256((r/name).read_bytes()).hexdigest()for name in fixtures}
(out/'dump.bin').unlink(missing_ok=True)
report={'result':'PASS','release_sha256':hashlib.sha256(binary).hexdigest(),'machine':'STE 68000 8 MHz, 1 MiB, RGB PAL, German TOS 1.62','selector_calls':5,'checks':['mouse cancel','mouse file selection','size and exact sanitized preview','mouse subdirectory navigation','TXT and all-files filters','reopen','keyboard exit to TOS','input files unchanged']}
(out/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
