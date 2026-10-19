"""Actual production DMA/VBL cycle cost, idle/both rates/source-rate conversion."""
from pathlib import Path
import os,sys,time,json,hashlib,subprocess,tempfile,socket,bisect
os.environ.setdefault('SDL_VIDEODRIVER','dummy');os.environ.setdefault('SDL_AUDIODRIVER','dummy')
sys.path.insert(0,str(Path.home()/'.agents/skills/hatari-debugging/scripts'))
from hatari_session import HatariSession,nm_symbols
from hrdb_profile import Rdb,profile_lines
root=Path(__file__).resolve().parents[1];baseline='--baseline'in sys.argv
prg=root/'analysis'/('BASE.PRG'if baseline else'BENCH.PRG');initial_sha=hashlib.sha256(prg.read_bytes()).hexdigest();sym=nm_symbols(str(prg),nm='m68k-atari-mintelf-nm')
textnames=sorted(set(int(line.split()[0],16)for line in subprocess.check_output(['m68k-atari-mintelf-nm','-n',str(prg)],text=True).splitlines()if len(line.split())==3 and line.split()[1]in('T','t')))
# Isolate this session from other tools/emulators using the shared HRDB port.
port=56129;probe=socket.socket();probe.bind(('127.0.0.1',port));probe.close()
with tempfile.TemporaryDirectory(prefix='amixer-profile-')as tmp:
 src=Path(tmp)/'port.c';dylib=Path(tmp)/'port.dylib'
 template=(root/'analysis/hrdb-port.c').read_text().replace('56129',str(port))
 src.write_text(template);subprocess.run(['cc','-dynamiclib','-O2',str(src),'-o',str(dylib)],check=True)
 os.environ['DYLD_INSERT_LIBRARIES']=str(dylib)
 emulator='/opt/homebrew/opt/hatari-hrdb/Applications/hatari-hrdb/Hatari-HRDB.app/Contents/MacOS/Hatari'
 with HatariSession(str(prg),hatari=emulator,tos=str(Path.home()/'Atari/tos/TOS v1.62 (1990)(Atari Corp)(STE)(De).img'),machine='ste',sound=False,extra_args=['--confirm-quit','false','--memsize','1','--cpuclock','8','--cpulevel','0','--monitor','rgb'])as h:
  h.wait(8);base=h.basepage()['text'];a=lambda n:base+sym[n]
  r=Rdb(port=port);results=[]
  symbols=sorted((addr,name)for name,addr in sym.items())
  def function(pc):
   matches=[(addr,name)for addr,name in symbols if addr<=pc-base]
   return matches[-1][1]if matches else'outside'
  # Use complete routine ranges, not nearest local/internal labels.
  names=['clear','framesLeft','fill','AudioMixer_Vbl','Memory_Clear','Memory_ClearMajor','Memory_ClearSimple_16','AudioMixer_Core','__mulsi3','__udivsi3','__divsi3']
  ranges={n:(a(n),base+next((v for v in textnames if v>sym[n]),sym[n]+1))for n in names if n in sym}
  # Core contains local labels, so its end is explicitly exported by the bench's copy or found by size.
  for index in range(10):
   h.debug('w $%x 0 %d'%(a('gBenchCase'),index),settle=.4)
   data=h.mem(a('gBenchReady'),2);assert data.u16(a('gBenchReady'))==index
   r.cmd('break',wait=.5);r.cmd('profile 1',wait=.1);r.cmd('run',wait=.1);h.wait(3);r.cmd('break',wait=1)
   msg=r.take('!profile')
   for _ in range(8):
    if msg:break
    r.pump(.5);msg=r.take('!profile')
   assert msg,'No profiler data';rows=profile_lines(msg);assert rows
   calls=sum(n for pc,n,c in rows if pc==a('AudioMixer_Vbl'));assert calls>50,calls
   components={name:sum(c for pc,n,c in rows if lo<=pc<hi)for name,(lo,hi)in ranges.items()}
   total=sum(components.values());totalcycles=sum(c for pc,n,c in rows)
   assert abs(totalcycles/calls-160256)<2500,('profile clock gap',totalcycles/calls)
   rate=12517 if index<3 or index in(7,8)else 25033
   voices=index if index<3 else(index-3 if index<6 else 2)
   item={'case':index,'output_Hz':rate,'voices':voices,'source_Hz':12517 if index==6 else(25033 if index==7 else rate),'clipping_stress':index>=8,'VBLs':calls,'cycles_per_VBL':total/calls,'ms_per_VBL':total/calls/8000,'percent_frame':100*total/calls/160256,'components_cycles_per_VBL':{n:c/calls for n,c in components.items()},'profile_total_cycles_per_VBL':totalcycles/calls}
   results.append(item);print(json.dumps(item),flush=True)
   # Keep profiling active between windows: HRDB preserves prev_cycles across
   # starts, so disabling trace here would charge the idle gap to the next PC.
   if index==9:r.cmd('profile 0',wait=.1)
   r.cmd('run',wait=.1)
  r.s.close()
 assert hashlib.sha256(prg.read_bytes()).hexdigest()==initial_sha,'Program changed during profiling'
 report={'program_sha256':initial_sha,'configuration':'STE, 68000, 8 MHz, 1 MiB, PAL RGB, German TOS 1.62','method':'HRDB instruction cycles for complete AMIXER VBL/controller/ASM and shared zero-fill/math helpers; busy main, no graphics/IO/control changes during measurement. About 3 seconds per case. Divide by actual callback entries and 160256 PAL cycles per VBL. Init/Play/gain table preparation and common interrupt dispatcher excluded.','baseline':baseline,'source_sha256':{n:hashlib.sha256(((root/'analysis/baseline'/n)if baseline else(root.parent.parent/'godlib/audio'/n)).read_bytes()).hexdigest()for n in('amixer.c','amixer_s.s')},'results':results}
 (root/'analysis'/('profile-before.json'if baseline else'profile.json')).write_text(json.dumps(report,indent=2)+'\n')
