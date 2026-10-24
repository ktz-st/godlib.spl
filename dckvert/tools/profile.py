from pathlib import Path
import sys,os,time,json,tempfile
os.environ['SDL_VIDEODRIVER']='dummy';os.environ['SDL_AUDIODRIVER']='dummy'
sys.path.insert(0,'/Users/kriss/.agents/skills/hatari-debugging/scripts')
from hatari_session import HatariSession,nm_symbols
from hrdb_profile import Rdb,profile_lines
r=Path(tempfile.mkdtemp(prefix='dckvert-profile-'));app=Path(__file__).resolve().parents[1];sy=nm_symbols('/tmp/DCKVDBG.PRG',nm='m68k-atari-mintelf-nm');results=[]
with HatariSession('/tmp/DCKVDBG.PRG',hatari='/opt/homebrew/opt/hatari-hrdb/Applications/hatari-hrdb/Hatari-HRDB.app/Contents/MacOS/Hatari',tos='/Users/kriss/Atari/tos/TOS v1.62 (1990)(Atari Corp)(STE)(De).img',machine='ste',screenshot_dir=str(r),extra_args=['--confirm-quit','false','--memsize','4','--cpulevel','0','--cpuclock','8','--monitor','rgb','--fast-forward','true'])as h:
 h.wait(3);base=h.basepage()['text'];a=lambda n:base+sy[n]
 def raw(addr,size):
  p=r/'state.bin';p.unlink(missing_ok=True);h.debug(f'savebin {p} ${addr:x} ${size:x}',settle=.08)
  for _ in range(100):
   if p.exists()and p.stat().st_size==size:return p.read_bytes()
   time.sleep(.01)
  raise RuntimeError(h.lines[-20:])
 def word(n):return int.from_bytes(raw(a(n),2),'big')
 for _ in range(60):
  if word('gVertReady')==1:break
  h.wait(.3)
 assert word('gVertReady')==1,h.lines[-25:]
 # Pause, then verify native output against atlas-derived four-plane pixels.
 h.debug(f'w ${a("gVertPaused"):x} 0 1');h.wait(.2)
 state=raw(a('gVertState'),48);rows=raw(a('gVertRows'),3456);screen=int.from_bytes(raw(a('gVertScreen'),4),'big');pixels=raw(screen,32000)
 from PIL import Image
 atlas=Image.open(app/'source/BIG.png');errors=0
 for lane,x0 in enumerate([48,144,240]):
  head=int.from_bytes(state[lane*16+12:lane*16+14],'big')
  for y in range(144):
   off=(lane*288+head+y)*4;p=int.from_bytes(rows[off:off+4],'big')-a('Vert_Font');assert 0<=p<=31360-20 and p%20==0
   glyph=p//640;row=(p%640)//20
   for x in range(40):
    sx=x0+x;screen_y=28+y;off=screen_y*160+(sx//16)*8;actual=sum(((int.from_bytes(pixels[off+q*2:off+q*2+2],'big')>>(15-sx%16))&1)<<q for q in range(4));expected=atlas.getpixel((glyph%8*40+x,glyph//8*32+row))if glyph<48 else 0;errors+=actual!=expected
 print('pixel mismatches',errors,flush=True);assert not errors
 h.screenshot();h.debug(f'w ${a("gVertHold"):x} 0 1');h.wait(.2);rdb=Rdb(port=int(os.environ.get('DCKV_HRDB_PORT','56001')))
 for count in (1,2,3):
  rdb.cmd('break',wait=.15);rdb.cmd(f'memset {a("gVertCompleted"):x} 2 0000',wait=.04);rdb.cmd(f'memset {a("gVertRequest"):x} 2 {count:04x}',wait=.04);rdb.cmd('profile 1',wait=.05);rdb.cmd('run',wait=.05);h.wait(1)
  rdb.cmd('break',wait=.2);msg=rdb.take('!profile')
  for _ in range(10):
   if msg:break
   rdb.pump(.2);msg=rdb.take('!profile')
  rows=profile_lines(msg);assert rows
  ranges=[(a('Vert_Advance'),a('Vert_RuntimeEnd'))]
  cycles=sum(c for pc,n,c in rows if any(lo<=pc<hi for lo,hi in ranges));draws=sum(n for pc,n,c in rows if pc==a('Vert_Draw'));assert draws==32,draws
  rdb.cmd('profile 0',wait=.05);rdb.cmd('run',wait=.05)
  assert word('gVertCompleted')==count
  item={'lanes':count,'draws':draws,'cycles_per_update':cycles/32,'ms_8mhz':cycles/32/8000,'pal_frame_percent':cycles/32/1600};results.append(item);print(item,flush=True)
 rdb.s.close();(app/'profiling.json').write_text(json.dumps({'pixel_mismatches':errors,'profiles':results},indent=2)+'\n')
 h.debug(f'w ${a("gVertHold"):x} 0 0');h.wait(.2);h.control('hatari-event keydown 01');h.wait(.2);h.control('hatari-event keyup 01');h.wait(.2);print('exit flag',word('gVertExited'),flush=True);assert word('gVertExited')==1
 (r/'hatari.log').write_text('\n'.join(h.lines))
