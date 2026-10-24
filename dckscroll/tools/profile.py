from pathlib import Path
import sys,os,time,json,tempfile
os.environ['SDL_VIDEODRIVER']='dummy';os.environ['SDL_AUDIODRIVER']='dummy'
sys.path.insert(0,'/Users/kriss/.agents/skills/hatari-debugging/scripts')
from hatari_session import HatariSession,nm_symbols
from hrdb_profile import Rdb,profile_lines
r=Path(tempfile.mkdtemp(prefix='dckscroll-profile-'));app=Path(__file__).resolve().parents[1];sy=nm_symbols('/tmp/DCKDBG.PRG',nm='m68k-atari-mintelf-nm');results=[]
with HatariSession('/tmp/DCKDBG.PRG',hatari='/opt/homebrew/opt/hatari-hrdb/Applications/hatari-hrdb/Hatari-HRDB.app/Contents/MacOS/Hatari',tos='/Users/kriss/Atari/tos/TOS v1.62 (1990)(Atari Corp)(STE)(De).img',machine='ste',screenshot_dir=str(r),extra_args=['--confirm-quit','false','--memsize','4','--cpulevel','0','--cpuclock','8','--monitor','rgb','--fast-forward','true'])as h:
 h.wait(3);base=h.basepage()['text'];a=lambda n:base+sy[n]
 def raw(addr,size):
  p=r/'state.bin';p.unlink(missing_ok=True);h.debug(f'savebin {p} ${addr:x} ${size:x}',settle=.08)
  for _ in range(100):
   if p.exists()and p.stat().st_size==size:return p.read_bytes()
   time.sleep(.01)
  raise RuntimeError(h.lines[-20:])
 def word(n):return int.from_bytes(raw(a(n),2),'big')
 for _ in range(60):
  if word('gDckReady')==1:break
  h.wait(.3)
 assert word('gDckReady')==1,h.lines[-25:]
 # Pause, then verify native output against atlas-derived four-plane pixels.
 h.debug(f'w ${a("gDckPaused"):x} 0 1');h.wait(.2)
 state=raw(a('gDckState'),48);cols=raw(a('gDckColumns'),960);screen=int.from_bytes(raw(a('gDckScreen'),4),'big');pixels=raw(screen,32000);font=(app/'assets/FONT.BIN').read_bytes();paths=json.loads((app/'assets/source.json').read_text())['curves'];errors=0
 for lane in range(3):
  head=int.from_bytes(state[lane*16+12:lane*16+14],'big')
  for col,y0 in enumerate(paths[lane]):
   off=(lane*80+head+col)*4;p=int.from_bytes(cols[off:off+4],'big')-a('Dck_Font');assert 0<=p<=len(font)-128
   for row in range(32):
    plane=font[p+row*4:p+row*4+4]
    for bit in range(8):
     x=col*8+bit;y=y0+row;off=y*160+(x//16)*8;actual=sum(((int.from_bytes(pixels[off+q*2:off+q*2+2],'big')>>(15-x%16))&1)<<q for q in range(4));expected=sum(((plane[q]>>(7-bit))&1)<<q for q in range(4));errors+=actual!=expected
 print('pixel mismatches',errors,flush=True);assert not errors
 h.screenshot();h.debug(f'w ${a("gDckHold"):x} 0 1');h.wait(.2);rdb=Rdb(port=int(os.environ.get('DCK_HRDB_PORT','56001')))
 for count in (1,2,3):
  rdb.cmd('break',wait=.15);rdb.cmd(f'memset {a("gDckCompleted"):x} 2 0000',wait=.04);rdb.cmd(f'memset {a("gDckRequest"):x} 2 {count:04x}',wait=.04);rdb.cmd('profile 1',wait=.05);rdb.cmd('run',wait=.05);h.wait(1)
  rdb.cmd('break',wait=.2);msg=rdb.take('!profile')
  for _ in range(10):
   if msg:break
   rdb.pump(.2);msg=rdb.take('!profile')
  rows=profile_lines(msg);assert rows
  ranges=[(a('Dck_Advance'),a('Dck_RuntimeEnd')),(a('gDckCode'),a('gDckCode')+23286)]
  cycles=sum(c for pc,n,c in rows if any(lo<=pc<hi for lo,hi in ranges));draws=sum(n for pc,n,c in rows if pc==a('Dck_Draw'));assert draws==32,draws
  rdb.cmd('profile 0',wait=.05);rdb.cmd('run',wait=.05)
  assert word('gDckCompleted')==count
  item={'lanes':count,'draws':draws,'cycles_per_update':cycles/32,'ms_8mhz':cycles/32/8000,'pal_frame_percent':cycles/32/1600};results.append(item);print(item,flush=True)
 rdb.s.close();(app/'profiling.json').write_text(json.dumps({'pixel_mismatches':errors,'profiles':results},indent=2)+'\n')
 h.debug(f'w ${a("gDckHold"):x} 0 0');h.wait(.2);h.control('hatari-event keydown 01');h.wait(.2);h.control('hatari-event keyup 01');h.wait(.2);print('exit flag',word('gDckExited'),flush=True);assert word('gDckExited')==1
 (r/'hatari.log').write_text('\n'.join(h.lines))
