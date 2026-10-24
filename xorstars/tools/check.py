from pathlib import Path
import sys,os,time,json,tempfile,struct
os.environ['SDL_VIDEODRIVER']='dummy';os.environ['SDL_AUDIODRIVER']='dummy'
sys.path.insert(0,str(Path.home()/'.agents/skills/hatari-debugging/scripts'))
from hatari_session import HatariSession,nm_symbols,SCANCODES
app=Path(__file__).resolve().parents[1];sy=nm_symbols('/tmp/XORDBG.PRG',nm='m68k-atari-mintelf-nm');r=Path(tempfile.mkdtemp(prefix='xorstars-controls-'))
with HatariSession('/tmp/XORDBG.PRG',hatari='/opt/homebrew/opt/hatari/Hatari.app/Contents/MacOS/hatari',tos=str(Path.home()/'Atari/tos/TOS v1.62 (1990)(Atari Corp)(STE)(De).img'),machine='ste',extra_args=['--confirm-quit','false','--memsize','4','--cpulevel','0','--cpuclock','8','--monitor','rgb','--fast-forward','true'])as h:
 h.wait(3);base=h.basepage()['text'];a=lambda n:base+sy[n]
 def raw(addr,size):
  p=r/'data.bin';p.unlink(missing_ok=True);h.debug(f'savebin {p} ${addr:x} ${size:x}',settle=.08)
  for _ in range(100):
   if p.exists()and p.stat().st_size==size:return p.read_bytes()
   time.sleep(.01)
  raise RuntimeError(h.lines[-20:])
 # Hex is intentional: Hatari strtol(base=0) rejects zero-padded "08".
 def tap(key):
  code=SCANCODES[key]
  h.control(f'hatari-event keydown 0x{code:x}');h.wait(.06)
  h.control(f'hatari-event keyup 0x{code:x}');h.wait(.15)
 def val(n,size=2):return int.from_bytes(raw(a(n),size),'big')
 def put(n,v):h.debug(f'w ${a(n):x} ${(v>>8)&255:x} ${v&255:x}',settle=.05)
 def pause():
  put('gXorPaused',1);h.wait(.1);put('gXorHold',1);h.wait(.1)
 def run():put('gXorHold',0);h.wait(.1)
 assert val('gXorReady')==1
 f0=val('gXorFrames',4);m0=val('gXorMissedVbl',4);h.wait(3);f1=val('gXorFrames',4);m1=val('gXorMissedVbl',4)
 result={'frames':f1-f0,'missed_vbls':m1-m0,'estimated_fps':50*(f1-f0)/(f1-f0+m1-m0),'double_buffer_references':0,'byte_mismatches':0,'keys':[]}
 def check():
  expected=bytearray(raw(val('gXorBack',4),32000));ss=list(struct.iter_unpack('>3H',raw(a('gXorStars'),1536)))
  for x,y,s in ss[:val('gXorCount')]:
   assert 0<=x<320 and 28<=y<172 and 1<=s<=4
   off=y*160+(x//16)*8+2;word=int.from_bytes(expected[off:off+2],'big')^(0x8000>>(x&15));expected[off:off+2]=word.to_bytes(2,'big')
  # sScreenClass starts with mem base, then its physical page pointers.
  pages=struct.unpack('>2I',raw(a('gScreenClass')+4,8))
  for ptr in pages:
   actual=raw(ptr,32000);errors=sum(x!=y for x,y in zip(actual,expected));assert errors==0,errors
   result['double_buffer_references']+=1
 pause();check()
 for key,mode in [('1',0),('2',1),('3',2),('4',3),('RIGHT',0),('LEFT',1),('DOWN',2),('UP',3)]:
  run();tap(key);h.wait(.2);pause();value=val('gXorMode');print('mode key',key,value,flush=True);assert value==mode,(key,value,mode);check();result['keys'].append(key)
 for key,count in [('5',64),('6',128),('7',256),('5',64),('7',256)]:
  run();tap(key);h.wait(.2);pause();value=val('gXorCount');print('count key',key,value,flush=True);assert value==count,(key,value,count);check();result['keys'].append(key)
 frozen=raw(a('gXorStars'),1536);run();h.wait(.2);pause();assert raw(a('gXorStars'),1536)==frozen;result['pause_freezes_state']=True
 run();tap('SPACE');h.wait(.2);assert val('gXorPaused')==0;put('gXorHold',1);h.wait(.1);assert raw(a('gXorStars'),1536)!=frozen;result['resumed']=True
 run();h.control('hatari-event keydown 01');h.wait(.15);h.control('hatari-event keyup 01');h.wait(.2);assert val('gXorExited')==1;result['exit']=True
 (app/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(result,flush=True)
