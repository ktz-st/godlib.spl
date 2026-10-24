from pathlib import Path
import os,sys,time,struct,json,random,tempfile,subprocess
os.environ['SDL_VIDEODRIVER']='dummy';os.environ['SDL_AUDIODRIVER']='dummy'
sys.path.insert(0,str(Path.home()/'.agents/skills/hatari-debugging/scripts'))
from hatari_session import HatariSession,nm_symbols
app=Path(__file__).resolve().parents[1];workspace=app.parents[1];r=Path(tempfile.mkdtemp(prefix='sndh-dck-psg-check-'));mini=workspace/'libcmini'
subprocess.run(['m68k-atari-mintelf-gcc','-Os','-Wall','-mshort','-mfastcall','-m68000','-fpack-struct=2','-I'+str(workspace),'-I'+str(mini/'include'),'-nostdlib','-nostartfiles','-nodefaultlibs','-static','-Wl,--gc-sections','-Wl,--relax','-L'+str(mini/'lib/mshort/mfastcall'),'-L'+str(workspace/'godlib'),'-o',str(r/'PSGTEST.PRG'),str(mini/'lib/mshort/mfastcall/crt0.o'),str(app/'tools/dck_psg_fixture.c'),str(app/'dckpsg_s.o'),'-Wl,--start-group','-lgod','-lcmini','-lgcc','-Wl,--end-group'],check=True)
sy=nm_symbols(str(r/'PSGTEST.PRG'),nm='m68k-atari-mintelf-nm')
with HatariSession(str(r/'PSGTEST.PRG'),hatari='/opt/homebrew/opt/hatari/Hatari.app/Contents/MacOS/hatari',tos=str(Path.home()/'Atari/tos/TOS v1.62 (1990)(Atari Corp)(STE)(De).img'),extra_args=['--confirm-quit','false','--memsize','4','--cpulevel','0','--cpuclock','8','--fast-forward','true'])as h:
 h.wait(3);base=h.basepage()['text'];a=lambda n:base+sy[n]
 def raw(addr,size):
  p=r/'data.bin';p.unlink(missing_ok=True);h.debug(f'savebin {p} ${addr:x} ${size:x}',settle=.02)
  for _ in range(100):
   if p.exists()and p.stat().st_size==size:return p.read_bytes()
   time.sleep(.005)
  raise RuntimeError(h.lines[-20:])
 def word(n):return int.from_bytes(raw(a(n),2),'big')
 def put(n,v):h.debug(f'w ${a(n):x} ${(v>>8)&255:x} ${v&255:x}',settle=.01)
 assert word('gTestReady')==1
 blank=raw(a('gTestBuffers'),32004);rng=random.Random(20261024)
 cases=[[v]*3 for v in range(17)]+[[v]*3 for v in range(16,-1,-1)]+[[0]*3,[16]*3,[0]*3,[16]*3,[16]*3,[16]*3]+[[rng.randrange(17)for _ in range(3)]for _ in range(8)]
 total=0
 for style in range(5):
  peak=style==4;put('gTestPeak',int(peak));style=min(style,3);expected_levels=[0]*3
  put('gTestStyle',style);put('gTestReset',1)
  active_cases=([(16,8,2)]*4+[(0,0,0)]*40+[(i%17,(i*3)%17,(i*7)%17)for i in range(20)])if peak else cases
  for n,levels in enumerate(active_cases):
   h.debug(f'w ${a("gPsgLevels"):x} '+' '.join(f'0 ${v:x}'for v in levels),settle=.01);request=n+1;put('gTestDone',0);put('gTestRequest',request)
   for _ in range(100):
    if word('gTestDone')==request:break
    h.wait(.01)
   assert word('gTestDone')==request
   expected=bytearray(blank)
   if peak:expected_levels=[max(max(v-1,0),levels[i])for i,v in enumerate(expected_levels)]
   else:expected_levels=list(levels)
   assert list(struct.unpack('>3H',raw(a('gPsgDckLevels'),6)))==expected_levels
   for ch,level in enumerate(expected_levels):
    if style==0:points=((x,y)for y in range(64+ch*32,74+ch*32)for x in range(32,32+level*16))
    else:
     width=[16,32,80][style-1];xx=[[120,152,184],[80,144,208],[24,120,216]][style-1][ch];scale=[2,4,4][style-1]
     points=((x,168-2*unit)for unit in range(level*scale)for x in range(xx,xx+width))
    for x,y in points:
     off=2+y*160+(x//16)*8+ch*2;v=int.from_bytes(expected[off:off+2],'big')|(0x8000>>(x&15));expected[off:off+2]=v.to_bytes(2,'big')
   actual=raw(a('gTestBuffers')+(n%2)*32004,32004)
   assert actual==expected,(style,n,levels,sum(x!=y for x,y in zip(actual,expected)))
   total+=1
  print('style',style,'peak'if peak else'render','passed',len(active_cases),'frames',flush=True)
 (r/'fixture-results.json').write_text(json.dumps({'styles':4,'peak_decay_test':True,'frames':total,'bytes_compared_per_frame':32004,'mismatches':0},indent=2)+'\n')
