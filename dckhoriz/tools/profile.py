from pathlib import Path
import sys,os,time,json,tempfile
os.environ['SDL_VIDEODRIVER']='dummy';os.environ['SDL_AUDIODRIVER']='dummy'
sys.path.insert(0,str(Path.home()/'.agents/skills/hatari-debugging/scripts'))
from hatari_session import HatariSession,nm_symbols
from hrdb_profile import Rdb,profile_lines
from PIL import Image
app=Path(__file__).resolve().parents[1];cfg=json.loads((app/'source/config.json').read_text());lanes=cfg['lanes'];dbg='/tmp/DCKHDBG.PRG'if lanes==1 else'/tmp/DCKMDBG.PRG';sy=nm_symbols(dbg,nm='m68k-atari-mintelf-nm');results=[];r=Path(tempfile.mkdtemp(prefix=app.name+'-profile-'))
with HatariSession(dbg,hatari='/opt/homebrew/opt/hatari-hrdb/Applications/hatari-hrdb/Hatari-HRDB.app/Contents/MacOS/Hatari',tos=str(Path.home()/'Atari/tos/TOS v1.62 (1990)(Atari Corp)(STE)(De).img'),machine='ste',screenshot_dir=str(r),extra_args=['--confirm-quit','false','--memsize','4','--cpulevel','0','--cpuclock','8','--monitor','rgb','--fast-forward','true'])as h:
 h.wait(3);base=h.basepage()['text'];a=lambda n:base+sy[n]
 def raw(addr,size):
  p=r/'state.bin';p.unlink(missing_ok=True);h.debug(f'savebin {p} ${addr:x} ${size:x}',settle=.08)
  for _ in range(100):
   if p.exists()and p.stat().st_size==size:return p.read_bytes()
   time.sleep(.01)
  raise RuntimeError(h.lines[-20:])
 def word(n):return int.from_bytes(raw(a(n),2),'big')
 for _ in range(60):
  if word('gHSReady')==1:break
  h.wait(.3)
 assert word('gHSReady')==1,h.lines[-25:]
 h.debug(f'w ${a("gHSPaused"):x} 0 1');h.wait(.2)
 state=raw(a('gHSState'),lanes*24);cols=raw(a('gHSColumns'),lanes*320);screen=int.from_bytes(raw(a('gHSScreen'),4),'big');pixels=raw(screen,32000);atlas=Image.open(app/'source/ESCALI.png');errors=0
 for lane,y0 in enumerate(cfg['y']):
  head=int.from_bytes(state[lane*24+12:lane*24+14],'big')
  assert cols[lane*320:lane*320+160]==cols[lane*320+160:lane*320+320]
  for col in range(40):
   off=(lane*80+head+col)*4;p=int.from_bytes(cols[off:off+4],'big')-a('HS_Font');assert 0<=p<=4736-64 and p%64==0
   glyph=p//128;part=(p%128)//64
   for row in range(16):
    for bit in range(8):
     x=col*8+bit;y=y0+row;off=y*160+(x//16)*8;actual=sum(((int.from_bytes(pixels[off+q*2:off+q*2+2],'big')>>(15-x%16))&1)<<q for q in range(4));expected=atlas.getpixel((glyph%20*16+part*8+bit,glyph//20*16+row))if glyph<36 else 0;errors+=actual!=expected
 print(app.name,'pixel mismatches',errors,flush=True);assert not errors
 h.screenshot();(app/'preview.png').write_bytes((r/'grab0001.png').read_bytes())
 h.debug(f'w ${a("gHSHold"):x} 0 1');h.wait(.2);rdb=Rdb(port=int(os.environ.get('HS_HRDB_PORT','56001')))
 for count in ([1]if lanes==1 else[1,3,6]):
  before=raw(a('gHSState'),lanes*24)
  rdb.cmd('break',wait=.15);rdb.cmd(f'memset {a("gHSCompleted"):x} 2 0000',wait=.04);rdb.cmd(f'memset {a("gHSRequest"):x} 2 {count:04x}',wait=.04);rdb.cmd('profile 1',wait=.05);rdb.cmd('run',wait=.05);h.wait(1)
  rdb.cmd('break',wait=.2);msg=rdb.take('!profile')
  for _ in range(10):
   if msg:break
   rdb.pump(.2);msg=rdb.take('!profile')
  rows=profile_lines(msg);assert rows
  cycles=sum(c for pc,n,c in rows if a('HS_Advance')<=pc<a('HS_RuntimeEnd'));draws=sum(n for pc,n,c in rows if pc==a('HS_Draw'));assert draws==32,draws
  rdb.cmd('profile 0',wait=.05);rdb.cmd('run',wait=.05);assert word('gHSCompleted')==count
  after=raw(a('gHSState'),lanes*24)
  for lane in range(lanes):
   off=lane*24;head=int.from_bytes(before[off+12:off+14],'big');tick=int.from_bytes(before[off+16:off+18],'big')
   for _ in range(32):
    tick-=1
    if tick==0:tick=cfg['periods'][lane];head=(head+cfg['directions'][lane])%40
   assert int.from_bytes(after[off+12:off+14],'big')==head
   assert int.from_bytes(after[off+16:off+18],'big')==tick
  item={'lanes':count,'draws':draws,'cycles_per_update':cycles/32,'ms_8mhz':cycles/32/8000,'pal_frame_percent':cycles/32/1600};results.append(item);print(item,flush=True)
 rdb.s.close();(app/'profiling.json').write_text(json.dumps({'pixel_mismatches':errors,'pixels_checked':lanes*320*16,'directions_and_periods_checked':True,'profiles':results},indent=2)+'\n')
 h.debug(f'w ${a("gHSHold"):x} 0 0');h.wait(.2);h.control('hatari-event keydown 01');h.wait(.2);h.control('hatari-event keyup 01');h.wait(.2);assert word('gHSExited')==1
 (r/'hatari.log').write_text('\n'.join(h.lines))
