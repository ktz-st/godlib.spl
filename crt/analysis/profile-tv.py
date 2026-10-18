"""Profile all TV frames of one actual N-key off/on cycle with HRDB."""
import os,sys,json,hashlib
from pathlib import Path
os.environ.setdefault('SDL_VIDEODRIVER','dummy');os.environ.setdefault('SDL_AUDIODRIVER','dummy')
sys.path.insert(0,str(Path.home()/'.agents/skills/hatari-debugging/scripts'))
from hatari_session import HatariSession,nm_symbols
from hrdb_profile import Rdb,profile_lines
root=Path(__file__).resolve().parents[1];sym=nm_symbols(str(root/'analysis/CRTDBG.PRG'),nm='m68k-atari-mintelf-nm')
with HatariSession(str(root/'CRT.PRG'),hatari='hatari-hrdb',tos=str(Path.home()/'Atari/tos/TOS v1.62 (1990)(Atari Corp)(STE)(De).img'),machine='ste',sound=False,extra_args=['--confirm-quit','false','--memsize','1','--cpuclock','8','--monitor','rgb']) as h:
 h.wait(9);base=h.basepage()['text'];a=lambda n:base+sym[n];r=Rdb()
 h.tap('A')
 r.cmd('break',wait=1);r.cmd('profile 1');r.cmd('run');h.tap('N');h.wait(4);r.cmd('break',wait=2)
 data=profile_lines(r.take('!profile'));assert data
 rows={pc:(n,c)for pc,n,c in data};frames=rows[a('Crt_TvRender')][0];assert frames==4*len(json.loads((root/'assets/tvsteps.json').read_text()))+2,frames
 groups={name:sum(c for pc,n,c in data if a(name)<=pc<a(name+'End'))for name in ['Crt_TvRender','Crt_TvUpdate']}
 item={'machine':'STE, 68000, 8 MHz, 1 MiB, RGB PAL, German TOS 1.62','program_sha256':hashlib.sha256((root/'CRT.PRG').read_bytes()).hexdigest(),'method':'HRDB measured N-key off/on cycle. Only ASM renderer and TV command update; Screen_Update/VBL/input excluded. Palette swap, scene preparation/Memory_Copy/font calls are outside these address ranges. This is an average over transition frames, not a worst-case bound.','transition_frames':frames,'cycles':groups,'cycles_per_transition_frame':{k:round(v/frames,2)for k,v in groups.items()},'total_cycles_per_transition_frame':round(sum(groups.values())/frames,2),'percent_160000_cycle_frame':round(sum(groups.values())/frames/1600,3)}
 r.cmd('profile 0');r.cmd('run');r.s.close()
(root/'analysis/tv-profile.json').write_text(json.dumps(item,indent=2)+'\n');print(json.dumps(item,indent=2))
