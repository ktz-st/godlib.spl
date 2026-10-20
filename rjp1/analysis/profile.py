#!/usr/bin/env python3
"""HRDB cycle counts: both sequencers on identical 50 Hz input, and full mixer."""
from pathlib import Path
import os,sys,time,tempfile,shutil,subprocess,json
os.environ.setdefault('SDL_VIDEODRIVER','dummy');os.environ.setdefault('SDL_AUDIODRIVER','dummy')
sys.path.insert(0,str(Path.home()/'.agents/skills/hatari-debugging/scripts'))
from hatari_session import HatariSession,nm_symbols
from hrdb_profile import Rdb,profile_lines
root=Path(__file__).resolve().parents[1];out=root/'analysis';result={}
maps={str(p):nm_symbols(str(p),nm='m68k-atari-mintelf-nm') for p in [out/'RJPBENCH.PRG',out/'RJPDBG.PRG']}
emulator='/opt/homebrew/opt/hatari-hrdb/Applications/hatari-hrdb/Hatari-HRDB.app/Contents/MacOS/Hatari'
with tempfile.TemporaryDirectory(prefix='rjp-profile-') as tmp:
 tmp=Path(tmp);dylib=tmp/'port.dylib';subprocess.run(['cc','-dynamiclib','-O2',str(out/'hrdb-port.c'),'-o',str(dylib)],check=True);os.environ['DYLD_INSERT_LIBRARIES']=str(dylib)
 for mode,exe,debug in [('sequence',out/'RJPBENCH.PRG',out/'RJPBENCH.PRG'),('25k',root/'RJP1.PRG',out/'RJPDBG.PRG'),('12k',root/'RJP1.PRG',out/'RJPDBG.PRG'),('50k',root/'RJP1.PRG',out/'RJPDBG.PRG')]:
  sy=maps[str(debug)];folder=tmp/mode;folder.mkdir();run=folder/exe.name;shutil.copy2(exe,run)
  for p in list(root.glob('*.SNG'))+list(root.glob('*.INS')):shutil.copy2(p,folder/p.name)
  with HatariSession(str(run),hatari=emulator,tos=str(Path.home()/'Atari/tos/TOS v1.62 (1990)(Atari Corp)(STE)(De).img'),sound=False,screenshot_dir=str(out/'shots/profile'),debug_except='bus,address,illegal',extra_args=['--confirm-quit','false','--memsize','1','--cpuclock','8','--cpulevel','0','--monitor','rgb']) as h:
   h.wait(9);base=h.basepage()['text'];a=lambda n:base+sy[n]
   if mode in ['12k','50k']:
    scan='0x02' if mode=='12k' else '0x04';h.control('hatari-event keydown '+scan,settle=.2);h.control('hatari-event keyup '+scan,settle=.2);h.wait(2)
   def readvar(name):
    p=folder/'var.bin';p.unlink(missing_ok=True);h.debug(f'savebin {p} ${a(name):x} $4',settle=.15)
    return int.from_bytes(p.read_bytes(),'big')
   work=readvar('spPaulaWorkspace');workbytes=readvar('sPaulaWorkspaceBytes')
   r=Rdb(port=56124);r.cmd('break',wait=2);r.cmd('profile 1');r.cmd('run');h.wait(12);r.cmd('break',wait=3);msg=r.take('!profile')
   for _ in range(5):
    if msg:break
    r.pump(1);msg=r.take('!profile')
   rows=profile_lines(msg);assert rows
   def region(first,last):return sum(c for pc,n,c in rows if a(first)<=pc<a(last))
   counts={pc:n for pc,n,c in rows}
   def fn(name):
    following=min(v for v in sy.values() if v>sy[name]);return sum(c for pc,n,c in rows if a(name)<=pc<base+following)
   calls=counts.get(a('vd_tick' if mode=='sequence' else 'Rjp1_Tick'),0);assert calls>100,(mode,calls)
   native=region('RjpCore_Begin','RjpCore_End');item={'ticks':calls,'sequencer_cycles_per_tick':native/calls}
   if mode=='sequence':
    original=region('RjpBaseline_Begin','RjpBaseline_End');translator=fn('vd_translate')+fn('vd_translate_init');item.update(original_sequencer_cycles_per_tick=original/calls,translator_cycles_per_tick=translator/calls,original_total_cycles_per_tick=(original+translator)/calls,saved_percent=100*(original+translator-native)/(original+translator))
   else:
    mixer=region('paula_calc','paula_channel_0')+sum(c for pc,n,c in rows if work<=pc<work+workbytes);item.update(mixer_cycles_per_tick=mixer/calls,audio_cpu_percent=100*(native+mixer)/calls/160000)
   result[mode]=item;r.cmd('profile 0');r.cmd('run');r.s.close();print(mode,item,flush=True)
result['release_sha256']=__import__('hashlib').sha256((root/'RJP1.PRG').read_bytes()).hexdigest()
result['method']='HRDB instruction cycles, STE 68000 8 MHz PAL 1 MiB German TOS 1.62, JON subsong 1. 12s windows. Sequence comparison uses identical frames, no mixing, with voice snapshot/restore outside measured regions. Full audio includes native sequencer, Paula calc/mix regions AND dynamically generated mixer code inside its allocated workspace; excludes small outer wrappers and UI.'
(out/'profile.json').write_text(json.dumps(result,indent=2)+'\n')
