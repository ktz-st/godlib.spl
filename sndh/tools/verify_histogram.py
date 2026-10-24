from pathlib import Path
import sys,os,time,struct,json,tempfile,subprocess
os.environ['SDL_VIDEODRIVER']='dummy';os.environ['SDL_AUDIODRIVER']='dummy'
sys.path.insert(0,str(Path.home()/'.agents/skills/hatari-debugging/scripts'))
from hatari_session import HatariSession,nm_symbols
app=Path(__file__).resolve().parents[1];workspace=app.parents[1];r=Path(tempfile.mkdtemp(prefix='sndh-histogram-check-'));mini=workspace/'libcmini'
subprocess.run(['m68k-atari-mintelf-gcc','-Os','-Wall','-mshort','-mfastcall','-m68000','-fpack-struct=2','-I'+str(workspace),'-I'+str(mini/'include'),'-nostdlib','-nostartfiles','-nodefaultlibs','-static','-Wl,--gc-sections','-Wl,--relax','-L'+str(mini/'lib/mshort/mfastcall'),'-L'+str(workspace/'godlib'),'-o',str(r/'HVTEST.PRG'),str(mini/'lib/mshort/mfastcall/crt0.o'),str(app/'tools/histogram_fixture.c'),str(app/'histogram_s.o'),'-Wl,--start-group','-lgod','-lcmini','-lgcc','-Wl,--end-group'],check=True)
sy=nm_symbols(str(r/'HVTEST.PRG'),nm='m68k-atari-mintelf-nm')
with HatariSession(str(r/'HVTEST.PRG'),hatari='/opt/homebrew/opt/hatari/Hatari.app/Contents/MacOS/hatari',tos=str(Path.home()/'Atari/tos/TOS v1.62 (1990)(Atari Corp)(STE)(De).img'),extra_args=['--confirm-quit','false','--memsize','4','--cpulevel','0','--cpuclock','8','--fast-forward','true'])as h:
 h.wait(3);base=h.basepage()['text'];a=lambda n:base+sy[n]
 def raw(addr,size):
  p=r/'state.bin';p.unlink(missing_ok=True);h.debug(f'savebin {p} ${addr:x} ${size:x}',settle=.025)
  for _ in range(100):
   if p.exists()and p.stat().st_size==size:return p.read_bytes()
   time.sleep(.005)
  raise RuntimeError(h.lines[-20:])
 def word(n):return int.from_bytes(raw(a(n),2),'big')
 assert word('gTestReady')==1
 background=raw(a('gTestBuffers'),32004);assert background==raw(a('gTestBuffers')+32004,32004)
 levels=[0]*16;cases=[(i,0x10|i,0xf0|(15-i))for i in range(16)]+[(i, (i+5)%16,(i+10)%16)for i in range(16)]+[(7,7,7)]*40+[(0x10,0x80,0xff)]*24
 for n,vol in enumerate(cases):
  if n==64:levels=[0]*16;h.debug(f'w ${a("gTestReset"):x} 0 1',settle=.01)
  h.debug(f'w ${a("gTestInput"):x} '+' '.join(f'${v:x}'for v in vol),settle=.01)
  request=n+1;h.debug(f'w ${a("gTestRequest"):x} ${(request>>8)&255:x} ${request&255:x}',settle=.01)
  for _ in range(100):
   if word('gTestDone')==request:break
   h.wait(.01)
  assert word('gTestDone')==request
  levels=[max(v-1,0)for v in levels]
  for v in vol:levels[v&15]=32
  assert list(raw(a('gPsgHistogram'),16))==levels
  expected=bytearray(background)
  for col,height in enumerate(levels):
   for y in range(143,143-height,-1):off=2+y*160+(col+2)*8;expected[off:off+2]=b'\xff\xfe'
  actual=raw(a('gTestBuffers')+(n%2)*32004,32004);assert actual==expected,(n,sum(x!=y for x,y in zip(actual,expected)))
 print('PASS',len(cases),'full-buffer frames, including guard words, all levels, envelopes, decay/reset and both pages.',flush=True)
 (r/'fixture-results.json').write_text(json.dumps({'frames':len(cases),'bytes_compared_per_frame':32004,'mismatches':0,'reset_frame':64},indent=2)+'\n')
