"""Cycle profile of the live, no-frame-cache ASM renderer."""
from pathlib import Path
import os,sys,json,hashlib,subprocess,tempfile,socket
os.environ.setdefault('SDL_VIDEODRIVER','dummy');os.environ.setdefault('SDL_AUDIODRIVER','dummy')
sys.path.insert(0,str(Path.home()/'.agents/skills/hatari-debugging/scripts'))
from hatari_session import HatariSession,nm_symbols
from hrdb_profile import Rdb,profile_lines
root=Path(__file__).resolve().parents[1];sym=nm_symbols(str(root/'analysis/IRISDBG.PRG'),nm='m68k-atari-mintelf-nm')
# A private bind port avoids stopping or sampling another task's HRDB process.
port_probe=socket.socket();port_probe.bind(('127.0.0.1',56124));port_probe.close()
temp=tempfile.TemporaryDirectory(prefix='iris-hrdb-');interposer=Path(temp.name)/'port.dylib'
subprocess.run(['cc','-dynamiclib','-O2',str(root/'analysis/hrdb-port.c'),'-o',str(interposer)],check=True)
os.environ['DYLD_INSERT_LIBRARIES']=str(interposer)
emulator='/opt/homebrew/opt/hatari-hrdb/Applications/hatari-hrdb/Hatari-HRDB.app/Contents/MacOS/Hatari'
with HatariSession(str(root/'IRIS.PRG'),hatari=emulator,tos=str(Path.home()/'Atari/tos/TOS v1.62 (1990)(Atari Corp)(STE)(De).img'),machine='ste',sound=False,extra_args=['--confirm-quit','false','--memsize','1','--cpuclock','8','--cpulevel','0','--monitor','rgb'])as h:
 h.wait(9);base=h.basepage()['text'];a=lambda n:base+sym[n]
 h.tap('A',hold=.15,after=.2)
 assert not any('Failed to bind socket'in l for l in h.lines),h.lines
 r=Rdb(port=56124)
 try:
  r.cmd('break',wait=2)
  status=r.take('!status')
  for _ in range(10):
   if status and status[1]==b'0':break
   r.pump(.5);status=r.take('!status')
  assert status and status[1]==b'0',('HRDB did not stop',status)
  r.cmd('profile 1');r.cmd('run');h.wait(12);r.cmd('break',wait=3)
 except BaseException:
  print('HRDB exception, process status',h.proc.poll(),'log',h.lines[-30:],flush=True)
  raise
 msg=r.take('!profile')
 for _ in range(5):
  if msg:break
  r.pump(2);msg=r.take('!profile')
 if not msg:
  print('RDB',[(m[:5],len(m))for m in r.msgs],flush=True)
  print('Hatari',h.lines[-35:],flush=True)
  raise AssertionError('No HRDB profile notification')
 data=profile_lines(msg);assert data
 rows={pc:(n,c)for pc,n,c in data}
 calls=lambda n:rows.get(a(n),(0,0))[0]
 cost=lambda first,last:sum(c for pc,n,c in data if a(first)<=pc<a(last))
 # Use sorted T/t symbols to include complete named library routine bodies.
 ordered=sorted(set(sym.values()))
 def function(n):
  end=next(v for v in ordered if v>sym[n]);return sum(c for pc,nc,c in data if a(n)<=pc<base+end)
 groups={'geometry_direct':cost('Iris_Prepare','Iris_PrepareEnd'),'render_dispatch_and_C_clip':cost('Iris_Render','Iris_RenderEnd'),'fill_ASM':cost('Iris_Delta','Iris_DeltaEnd'),'scan_ASM':cost('Iris_Scan','Iris_ScanEnd'),'sparse_restore_ASM':cost('Iris_Restore','Iris_RestoreEnd'),'background_copy':cost('Iris_CopyRows','Iris_CopyRowsEnd'),'outline_ASM':cost('Iris_WhiteLine','Iris_WhiteLineEnd'),'shared_32bit_math':sum(function(n)for n in ('__mulsi3','__udivsi3','__divsi3'))}
 count=calls('Iris_Prepare');assert count>40,count
 item={'program_sha256':hashlib.sha256((root/'IRIS.PRG').read_bytes()).hexdigest(),'configuration':'STE, 68000, 8 MHz, 1 MiB, PAL RGB, German TOS 1.62','method':'HRDB instruction cycles. Automatic complete transitions; costs divided by Iris_Prepare calls. Includes both growing and shrinking and some idle dispatch; 32-bit helpers shared by C geometry/clipping are a separate bucket. VBL/Screen_Update/input, outer Prepare/Outcode helpers and picture/font setup excluded.','geometry_calls':count,'render_calls':calls('Iris_Render'),'fill_calls':calls('Iris_Delta'),'components':{k:{'cycles_per_geometry_update':v/count,'ms_per_geometry_update':v/count/8000}for k,v in groups.items()},'renderer_ms_per_update':sum(groups.values())/count/8000}
 r.cmd('profile 0');r.cmd('run');r.s.close()
(root/'analysis/profile.json').write_text(json.dumps(item,indent=2)+'\n');print(json.dumps(item,indent=2),flush=True)
