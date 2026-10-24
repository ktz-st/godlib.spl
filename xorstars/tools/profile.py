from pathlib import Path
import sys,os,time,json,tempfile,struct
os.environ['SDL_VIDEODRIVER']='dummy';os.environ['SDL_AUDIODRIVER']='dummy'
sys.path.insert(0,str(Path.home()/'.agents/skills/hatari-debugging/scripts'))
from hatari_session import HatariSession,nm_symbols
from hrdb_profile import Rdb,profile_lines
app=Path(__file__).resolve().parents[1];sy=nm_symbols('/tmp/XORDBG.PRG',nm='m68k-atari-mintelf-nm');results=[];r=Path(tempfile.mkdtemp(prefix='xorstars-profile-'))
with HatariSession('/tmp/XORDBG.PRG',hatari='/opt/homebrew/opt/hatari-hrdb/Applications/hatari-hrdb/Hatari-HRDB.app/Contents/MacOS/Hatari',tos=str(Path.home()/'Atari/tos/TOS v1.62 (1990)(Atari Corp)(STE)(De).img'),machine='ste',screenshot_dir=str(r),extra_args=['--confirm-quit','false','--memsize','4','--cpulevel','0','--cpuclock','8','--monitor','rgb','--fast-forward','true'])as h:
 h.wait(3);base=h.basepage()['text'];a=lambda n:base+sy[n]
 def raw(addr,size):
  p=r/'state.bin';p.unlink(missing_ok=True);h.debug(f'savebin {p} ${addr:x} ${size:x}',settle=.08)
  for _ in range(100):
   if p.exists()and p.stat().st_size==size:return p.read_bytes()
   time.sleep(.01)
  raise RuntimeError(h.lines[-20:])
 def word(n):return int.from_bytes(raw(a(n),2),'big')
 def put(n,v):h.debug(f'w ${a(n):x} ${(v>>8)&255:x} ${v&255:x}',settle=.06)
 def ptr(n):return int.from_bytes(raw(a(n),4),'big')
 def state():return list(struct.iter_unpack('>3H',raw(a('gXorStars'),1536)))
 def check():
  expected=bytearray(raw(ptr('gXorBack'),32000));actual=raw(ptr('gXorScreen'),32000);ss=state()
  for x,y,s in ss[:word('gXorCount')]:
   assert 0<=x<320 and 28<=y<172 and 1<=s<=4
   off=y*160+(x//16)*8+2;v=int.from_bytes(expected[off:off+2],'big')^(0x8000>>(x&15));expected[off:off+2]=v.to_bytes(2,'big')
  errors=sum(x!=y for x,y in zip(actual,expected));assert errors==0,errors
  return errors
 for _ in range(60):
  if word('gXorReady')==1:break
  h.wait(.3)
 assert word('gXorReady')==1,h.lines[-20:]
 put('gXorPaused',1);h.wait(.2);put('gXorHold',1);h.wait(.2)
 check();h.screenshot();(app/'preview.png').write_bytes((r/'grab0001.png').read_bytes());rdb=Rdb(port=int(os.environ.get('XOR_HRDB_PORT','56001')))
 for mode in range(4):
  for count in [64,128,256]:
   put('gXorMode',mode);put('gXorCount',count)
   # Prime density transitions outside the timed batch: old page count may differ.
   put('gXorCompleted',0);put('gXorRequest',2)
   for _ in range(30):
    if word('gXorCompleted')==2:break
    h.wait(.1)
   assert word('gXorCompleted')==2;check();before=state()
   rdb.cmd('break',wait=.12);rdb.cmd(f'memset {a("gXorCompleted"):x} 2 0000',wait=.03);rdb.cmd(f'memset {a("gXorRequest"):x} 2 0001',wait=.03);rdb.cmd('profile 1',wait=.04);rdb.cmd('run',wait=.04);h.wait(.7)
   rdb.cmd('break',wait=.2);msg=rdb.take('!profile')
   for _ in range(10):
    if msg:break
    rdb.pump(.2);msg=rdb.take('!profile')
   rows=profile_lines(msg);assert rows
   cycles=sum(c for pc,n,c in rows if a('Xor_Advance')<=pc<a('Xor_RuntimeEnd'));draws=sum(n for pc,n,c in rows if pc==a('Xor_Draw'));assert draws==32,draws
   rdb.cmd('profile 0',wait=.04);rdb.cmd('run',wait=.04);assert word('gXorCompleted')==1;check();after=state()
   for i,(x,y,s)in enumerate(before):
    if i<count:
     if mode==0:x=(x+s*32)%320
     if mode==1:x=(x-s*32)%320
     if mode==2:y=28+(y-28+s*32)%144
     if mode==3:y=28+(y-28-s*32)%144
    assert after[i]==(x,y,s),(mode,count,i,after[i],(x,y,s))
   item={'mode':['right','left','down','up'][mode],'stars':count,'draws':draws,'cycles_per_update':cycles/32,'ms_8mhz':cycles/32/8000,'pal_frame_percent':cycles/32/1600};results.append(item);print(item,flush=True)
 rdb.s.close();(app/'profiling.json').write_text(json.dumps({'full_frame_xor_references':25,'byte_mismatches':0,'all_modes_and_wrap_checked':True,'profiles':results},indent=2)+'\n')
 # Last case restores density 256, matching both normal-loop page counts.
 put('gXorHold',0);h.wait(.2);h.control('hatari-event keydown 01');h.wait(.2);h.control('hatari-event keyup 01');h.wait(.2);assert word('gXorExited')==1
 (r/'hatari.log').write_text('\n'.join(h.lines))
