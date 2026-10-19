"""Exercise native GUI/GuiFS through actual SDL mouse and IKBD keys in Hatari."""
from pathlib import Path
import hashlib,json,os,struct,subprocess,sys,tempfile,time
from PIL import Image
os.environ.setdefault('SDL_VIDEODRIVER','dummy');os.environ.setdefault('SDL_AUDIODRIVER','dummy')
sys.path.insert(0,str(Path.home()/'.agents/skills/hatari-debugging/scripts'))
from hatari_session import HatariSession,nm_symbols
r=Path(__file__).resolve().parents[1];out=r/'analysis'
sy=nm_symbols(str(out/'GUIDBG.PRG'),nm='m68k-atari-mintelf-nm')
fixtures={str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest()for p in (r/'DATA').rglob('*')if p.is_file()}
hatari='/opt/homebrew/opt/hatari/Hatari.app/Contents/MacOS/hatari'
with tempfile.TemporaryDirectory(prefix='godlib-gui-')as tmp:
 tmp=Path(tmp);lib=tmp/'input.dylib';fifo=tmp/'input.pipe';os.mkfifo(fifo)
 flags=subprocess.check_output(['pkg-config','--cflags','--libs','sdl2'],text=True).split()
 subprocess.run(['clang','-dynamiclib',str(out/'sdl-input.c'),*flags,'-o',str(lib)],check=True)
 os.environ['FSEL_INPUT_PIPE']=str(fifo);os.environ['DYLD_INSERT_LIBRARIES']=str(lib)
 pipe=os.open(fifo,os.O_RDWR|os.O_NONBLOCK)
 try:
  with HatariSession(str(r/'GUI.PRG'),hatari=hatari,tos=str(Path.home()/'Atari/tos/TOS v1.62 (1990)(Atari Corp)(STE)(De).img'),screenshot_dir=str(out/'shots'),debug_except='bus,address,illegal',extra_args=['--confirm-quit','false','--memsize','1','--cpuclock','8','--monitor','rgb'])as h:
   h.wait(9);base=h.basepage()['text'];a=lambda n:base+sy[n]
   def dump(address,size):
    p=out/'dump.bin';p.unlink(missing_ok=True);h.debug('savebin %s $%x $%x'%(p,address,size),settle=.04)
    for _ in range(100):
     if p.exists()and p.stat().st_size==size:return p.read_bytes()
     time.sleep(.01)
    raise AssertionError(('dump timeout',h.lines[-15:]))
   def word(n):return struct.unpack('>H',dump(a(n),2))[0]
   def long(n):return struct.unpack('>I',dump(a(n),4))[0]
   def text(address):return dump(address,128).split(b'\0')[0].decode('latin-1')
   def snap(name):Image.open(h.screenshot()).save(out/(name+'.png'))
   def motion(dx,dy):os.write(pipe,('m %d %d\n'%(dx,dy)).encode());h.wait(.12)
   def point(x,y):
    motion(-2000,-2000);motion(-2000,-2000);motion(x*2,y*2)
    actual=(word('gGuiMouseX'),word('gGuiMouseY'));assert actual==(x,y),(actual,(x,y))
   def press(state):os.write(pipe,('b %d 0\n'%state).encode());h.wait(.12)
   def click(x,y):point(x,y);press(1);press(0);h.wait(.25)
   def key(scan):h.control('hatari-event keydown '+str(scan),settle=.08);h.control('hatari-event keyup '+str(scan),settle=.08)
   tables=struct.unpack('>2I',dump(a('gIKBD'),8))
   normal,shifted=[dump(ptr,128)for ptr in tables]
   def typechar(c):
    value=ord(c)
    if value in normal:key(normal.index(value))
    else:
     scan=shifted.index(value)
     h.control('hatari-event keydown 42',settle=.08);key(scan);h.control('hatari-event keyup 42',settle=.08)
   stride=word('gGuiButtonSize');ws=word('gGuiWindowSize');no=word('gGuiNameOffset');to=word('gGuiTitleOffset')
   names={}
   for i in range(word('buttonCount')):
    address=a('buttons')+i*stride;name=text(struct.unpack('>I',dump(address+no,4))[0]);names[name]=address
   def bounds(address):return struct.unpack('>4h',dump(address+8,8))
   def hit(name):
    x,y,w,height=bounds(names[name]);click(x+w//2,y+height//2)
   def rows():
    header=dump(a('windows')+ws*3,ws);count=struct.unpack_from('>H',header,102)[0];ptr=struct.unpack_from('>I',header,108)[0]
    if not count:return {}
    result={}
    for address in struct.unpack('>'+str(count)+'I',dump(ptr,4*count)):
     title=struct.unpack('>I',dump(address+to,4))[0];result[text(title)]=address
    return result
   def hitrow(name):
    address=rows()[name];x,y,w,height=bounds(address);click(x+30,y+height//2)
   def current(var):return text(struct.unpack('>I',dump(a(var),4))[0])
   try:
    assert word('gGuiReady')==1,h.lines[-15:]
    assert long('gGuiGain')==50
    snap('main');hit('APPLY');assert word('gGuiApplyCount')==1
    hit('NAME');key(30);key(48);key(14);key(28) # append a,b, erase b, accept
    assert current('gGuiName')=='ATARIa',current('gGuiName')
    hit('GAIN_ADD');assert 51<=long('gGuiGain')<=60,long('gGuiGain')
    # Real thumb dragging and both endpoint clamps.
    x,y,w,height=bounds(names['GAIN_THUMB']);point(x+w//2,y+height//2);press(1);motion(500,0);press(0)
    assert long('gGuiGain')==100,long('gGuiGain')
    x,y,w,height=bounds(names['GAIN_THUMB']);point(x+w//2,y+height//2);press(1);motion(-500,0);press(0)
    assert long('gGuiGain')==0,long('gGuiGain')
    hit('RESET');assert long('gGuiGain')==50;assert current('gGuiName')=='ATARI'
    hit('OPEN');assert word('gGuiOpenCount')==1;assert word('gGuiListCount')==19,word('gGuiListCount')
    listing=rows();assert 'HELLO.TXT'in listing and 'IGNORE.DAT'not in listing and '>SUB'in listing
    snap('files')
    # Scroll enough to exercise rows outside the initial viewport.
    hit('FS_SUB');assert word('gGuiScrollY')>0,word('gGuiScrollY')
    snap('scrolled')
    hit('BUTT_FS_CANCEL');assert word('gGuiCallbacks')==1
    hit('OPEN');assert word('gGuiScrollY')==0
    hitrow('HELLO.TXT');hit('BUTT_FS_OK')
    assert word('gGuiCallbacks')==2
    assert text(a('gGuiSelected'))=='C:\\DATA\\HELLO.TXT',text(a('gGuiSelected'))
    snap('selected')
    hit('OPEN');hitrow('>SUB');assert set(rows())=={'SECOND.TXT'},rows()
    snap('subdirectory');hitrow('SECOND.TXT');hit('BUTT_FS_OK')
    assert text(a('gGuiSelected'))=='C:\\DATA\\SUB\\SECOND.TXT',text(a('gGuiSelected'))
    hit('OPEN');hit('BUTT_FOLDERBACK');baseline=long('gGuiTreeCount');hitrow('>EMPTY');assert not rows(),rows();snap('empty')
    # A zero-range scrollbar must remain safe, including clicks and dragging.
    hit('FS_SUB');hit('FS_ADD');assert word('gGuiScrollY')==0
    hit('BUTT_FOLDERBACK');assert len(rows())==19
    hit('BUTT_FILEMASK');key(14);key(14);key(14);key(14);key(14)
    typechar('*');typechar('.');typechar('*');key(28) # keypad '*', period, '*': *.*
    assert len(rows())==20 and 'IGNORE.DAT'in rows(),list(rows())
    snap('all-files');hit('BUTT_FS_CANCEL');assert word('gGuiCallbacks')==4
    for i in range(4):
     hit('OPEN');hit('BUTT_FOLDERBACK');assert len(rows())==19;assert long('gGuiTreeCount')==baseline;hit('BUTT_FS_CANCEL')
    assert word('gGuiCallbacks')==8
    point(319,199);point(0,0);point(319,0);point(0,199);point(160,100)
    hit('EXIT');h.wait(.7)
    assert h.basepage()['text']!=base,'did not return to TOS'
    assert word('gGuiExited')==1
    assert long('gGuiCleanupVars')==0,long('gGuiCleanupVars')
    snap('desktop')
    assert not any(any(e in line for e in ('Bus Error','Address Error','CPU exception'))for line in h.lines),h.lines[-20:]
   except BaseException:
    snap('failure');(out/'failure.log').write_text('\n'.join(h.lines));raise
 finally:os.close(pipe)

assert fixtures=={str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest()for p in (r/'DATA').rglob('*')if p.is_file()}
(out/'dump.bin').unlink(missing_ok=True)
report={'result':'PASS','release_sha256':hashlib.sha256((r/'GUI.PRG').read_bytes()).hexdigest(),'machine':'STE, 68000, 8 MHz, 1 MiB, German TOS 1.62','checks':['real SDL mouse and IKBD input','button callback','native text edit and backspace','slider arrows, drag and endpoint clamps','reset','TXT mask and all-files mask','file selection and full path','folder navigation and UP','empty directory and zero-range scrollbar','scrolling file list','8 selector callbacks and repeated reopen/cancel','cursor at all four edges','exit to TOS','fixtures unchanged']}
(out/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
