"""Compare complete native frames with independent shifted-pixel CRT reference."""
import os,sys,struct,time,json,random,shutil
from pathlib import Path
os.environ.setdefault('SDL_VIDEODRIVER','dummy');os.environ.setdefault('SDL_AUDIODRIVER','dummy')
sys.path.insert(0,str(Path.home()/'.agents/skills/hatari-debugging/scripts'))
from hatari_session import HatariSession,nm_symbols
root=Path(__file__).resolve().parents[1];sym=nm_symbols(str(root/'analysis/CRTDBG.PRG'),nm='m68k-atari-mintelf-nm')
raw=(root/'assets/INDICES.BIN').read_bytes();results=[];pages=set()
with HatariSession(str(root/'CRT.PRG'),tos=str(Path.home()/'Atari/tos/TOS v1.62 (1990)(Atari Corp)(STE)(De).img'),machine='ste',sound=False,screenshot_dir=str(root/'analysis/shots'),debug_except='bus,address,illegal',extra_args=['--confirm-quit','false','--memsize','1','--cpuclock','8','--monitor','rgb']) as h:
 h.wait(9);base=h.basepage()['text'];a=lambda n:base+sym[n]
 def stop():h.debug('b pc = $%x :once'%a('Crt_FrameDone'),settle=.12)
 def step():h.stdin_cmd('b pc = $%x :once'%a('Crt_FrameDone'),settle=.01);h.stdin_cmd('c',settle=.06)
 def dump(addr,n):
  f=root/'analysis/dump.bin';f.unlink(missing_ok=True);h.stdin_cmd('savebin %s $%x $%x'%(f,addr,n),settle=.02)
  for _ in range(200):
   if f.exists()and f.stat().st_size==n:break
   time.sleep(.01)
  data=f.read_bytes();assert len(data)==n;return data
 def write(addr,data):h.stdin_cmd('w $%x '%addr+' '.join('$%02x'%v for v in data),settle=.01)
 def u16(n):return struct.unpack('>H',dump(a(n),2))[0]
 def ptr(n):return struct.unpack('>I',dump(a(n),4))[0]
 stop();assert u16('gCrtReady')==1;write(a('gCrtPause'),b'\x00\x01')
 back=dump(ptr('gScreenBackGraphic'),32000)
 def check():
  shifts=struct.unpack('>11h',dump(a('gCrtX'),22));dy=struct.unpack('>h',dump(a('gCrtY'),2))[0];band=struct.unpack('>h',dump(a('gCrtBand'),2))[0];scan=u16('gCrtScan');out=bytearray(back)
  for y in range(16,192):
   sy=y-dy;dx=shifts[(y-16)//16]
   line=raw[sy*320:(sy+1)*320]if 0<=sy<200 else bytes(320)
   line=bytes(dx)+line[:320-dx]if dx>=0 else line[-dx:]+bytes(-dx)
   mask=bool(scan and y&1 and not band<=y-16<band+22)
   for x in range(0,320,16):
    vals=line[x:x+16];words=[sum(((v>>pl)&1)<<(15-j)for j,v in enumerate(vals))for pl in range(3)]+[65535 if mask else 0]
    struct.pack_into('>4H',out,y*160+x//16*8,*words)
  screen=ptr('gScreenLogicGraphic');actual=dump(screen,32000)
  if actual!=out:
   (root/'analysis/actual.bin').write_bytes(actual);(root/'analysis/expected.bin').write_bytes(out)
   raise AssertionError({'shift':shifts,'y':dy,'band':band,'first_difference':next((i,x,y)for i,(x,y)in enumerate(zip(actual,out))if x!=y)})
  assert dump(ptr('gScreenBackGraphic'),32000)==back,'Back modified'
  pages.add(screen);results.append({'x':shifts,'y':dy,'band':band,'scan':scan,'page':screen})
 cases=[]
 for dx in range(-7,9):
  for dy in [-1,0,1,2]:cases.append(([dx]*11,dy,(dx*13+dy*7)%220-22,1))
 rng=random.Random(68000)
 for _ in range(12):cases.append(([rng.randrange(-7,9)for _ in range(11)],rng.randrange(-1,3),rng.randrange(-22,198),1))
 cases +=[([0]*11,0,band,scan)for scan in [0,1]for band in [-32,-22,-1,0,1,154,175,176,198]]
 for shifts,dy,band,scan in cases:
  write(a('gCrtX'),struct.pack('>11h',*shifts));write(a('gCrtY'),struct.pack('>h',dy));write(a('gCrtBand'),struct.pack('>h',band));write(a('gCrtScan'),struct.pack('>H',scan))
  for _ in range(2):step();check()
 print('PASS',len(results),'native full-frame comparisons on both pages',flush=True)
 write(a('gCrtPause'),b'\x00\x00');h.stdin_cmd('c',settle=.1);h.wait(.5)
 normal=h.screenshot();shutil.copy2(normal,root/'analysis/preview.png');print('normal',normal,flush=True)
 h.tap('G');h.wait(.2);glitch=h.screenshot();shutil.copy2(glitch,root/'analysis/tearing.png');print('glitch',glitch,flush=True)
 h.tap('G');h.tap('A');h.tap('S');h.tap('B');h.tap('SPACE');h.wait(.3)
 h.control('hatari-event keydown 01');h.wait(.1);h.control('hatari-event keyup 01');h.wait(.5)
 assert h.mem(a('gCrtExited'),2).u16(a('gCrtExited'))==1
 assert len(pages)==2
 faults=[l for l in h.lines if any(s in l for s in ['Bus Error','Address Error','Illegal instruction'])];assert not faults,faults
 (root/'analysis/verification.json').write_text(json.dumps({'machine':'STE 8 MHz, 1 MiB, RGB PAL, German TOS 1.62','frames':len(results),'display_pages':len(pages),'tests':'All 16 X shifts -7..8, all four Y shifts -1..2, coalesced and independently torn bands, band edges, scanline toggle, immutable Back, controls and clean exit','cases':results},indent=2)+'\n')
 (root/'analysis/hatari.log').write_text('\n'.join(h.lines))
 (root/'analysis/dump.bin').unlink(missing_ok=True)
