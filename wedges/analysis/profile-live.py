"""Cycle profile of the live, no-frame-cache ASM renderer."""
from pathlib import Path
import os,sys,json,hashlib,subprocess,tempfile,socket
os.environ.setdefault('SDL_VIDEODRIVER','dummy');os.environ.setdefault('SDL_AUDIODRIVER','dummy')
sys.path.insert(0,str(Path.home()/'.agents/skills/hatari-debugging/scripts'))
from hatari_session import HatariSession,nm_symbols
from hrdb_profile import Rdb,profile_lines
root=Path(__file__).resolve().parents[1];sym=nm_symbols(str(root/'analysis/RTDBG.PRG'),nm='m68k-atari-mintelf-nm')
assert 'gWedgesCache'not in sym and 'Wedges_BuildFrames'not in sym
# A private bind port avoids stopping or sampling another task's HRDB process.
port_probe=socket.socket();port_probe.bind(('127.0.0.1',56123));port_probe.close()
temp=tempfile.TemporaryDirectory(prefix='wedges-hrdb-');interposer=Path(temp.name)/'port.dylib'
subprocess.run(['cc','-dynamiclib','-O2',str(root/'analysis/hrdb-port.c'),'-o',str(interposer)],check=True)
os.environ['DYLD_INSERT_LIBRARIES']=str(interposer)
emulator='/opt/homebrew/opt/hatari-hrdb/Applications/hatari-hrdb/Hatari-HRDB.app/Contents/MacOS/Hatari'
with HatariSession(str(root/'WEDGERT.PRG'),hatari=emulator,tos=str(Path.home()/'Atari/tos/TOS v1.62 (1990)(Atari Corp)(STE)(De).img'),machine='ste',sound=False,extra_args=['--confirm-quit','false','--memsize','1','--cpuclock','8','--cpulevel','0','--monitor','rgb'])as h:
 h.wait(9);base=h.basepage()['text'];a=lambda n:base+sym[n]
 # Sampling counters outside the measured interval also checks actual frame cadence.
 lo=min(a('gWedgesFrames'),a('gWedgesLastVbl'));hi=max(a('gWedgesFrames'),a('gWedgesLastVbl'))+4
 def sample():
  data=h.mem(lo,hi-lo);return data.u32(a('gWedgesFrames')),data.u32(a('gWedgesLastVbl'))
 f0,v0=sample()
 assert not any('Failed to bind socket'in l for l in h.lines),h.lines
 r=Rdb(port=56123)
 try:
  r.cmd('break',wait=2)
  status=r.take('!status')
  for _ in range(10):
   if status and status[1]==b'0':break
   r.pump(.5);status=r.take('!status')
  assert status and status[1]==b'0',('HRDB did not stop',status)
  r.cmd('profile 1');r.cmd('run');h.wait(8);r.cmd('break',wait=3)
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
 data=profile_lines(msg);assert data;rows={pc:(n,c)for pc,n,c in data}
 calls=lambda n:rows.get(a(n),(0,0))[0]
 cost=lambda first,last:sum(c for pc,n,c in data if a(first)<=pc<a(last))
 frames=calls('Wedges_Render');draws=calls('Wedges_Live');assert frames>100 and draws>100
 geometry=cost('Wedges_Live','Wedges_LiveEnd');controller=cost('Wedges_Render','Wedges_RenderEnd')
 item={'program_sha256':hashlib.sha256((root/'WEDGERT.PRG').read_bytes()).hexdigest(),'configuration':'STE, 68000, 8 MHz, 1 MiB, PAL RGB, German TOS 1.62','HRDB_port':56123,'method':'HRDB instruction cycles for complete live ASM geometry+raster routine and C render dispatch. Default speed 6 and same 32 angle phases as cached version; VBL/input/Screen_Update/animation control excluded. 8-second sample wait plus command settling. Frame budget uses 160000 cycles at nominal 50 Hz.','rendered_frames':frames,'draw_calls':draws,'frame_cache_bytes':0,'coordinate_history_bytes':4808,'constant_table_bytes':sym['Wedges_LiveTablesEnd']-sym['Wedges_LiveTables'],'kernel_cycles_per_call':geometry/draws,'controller_cycles_per_frame':controller/frames,'total_renderer_cycles_per_frame':(geometry+controller)/frames,'total_renderer_ms_per_frame':(geometry+controller)/frames/8000,'total_renderer_percent_of_160000_cycle_frame':(geometry+controller)/frames/1600}
 r.cmd('profile 0');r.cmd('run');r.s.close()
 f1,v1=sample();assert f1>f0 and v1>v0
 item.update(cadence_frame_delta=f1-f0,cadence_vbl_delta=v1-v0,updates_per_second_from_vbl=50*(f1-f0)/(v1-v0))
(root/'analysis/profile-live.json').write_text(json.dumps(item,indent=2)+'\n');print(json.dumps(item,indent=2),flush=True)
