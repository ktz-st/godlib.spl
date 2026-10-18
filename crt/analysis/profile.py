"""STE 8 MHz HRDB: include blitter work/wait and C parameter preparation."""
import os,sys,json,hashlib
from pathlib import Path
os.environ.setdefault('SDL_VIDEODRIVER','dummy');os.environ.setdefault('SDL_AUDIODRIVER','dummy')
sys.path.insert(0,str(Path.home()/'.agents/skills/hatari-debugging/scripts'))
from hatari_session import HatariSession,nm_symbols
from hrdb_profile import Rdb,profile_lines
root=Path(__file__).resolve().parents[1];sym=nm_symbols(str(root/'analysis/CRTDBG.PRG'),nm='m68k-atari-mintelf-nm');out=[]
with HatariSession(str(root/'CRT.PRG'),hatari='hatari-hrdb',tos=str(Path.home()/'Atari/tos/TOS v1.62 (1990)(Atari Corp)(STE)(De).img'),machine='ste',sound=False,extra_args=['--confirm-quit','false','--memsize','1','--cpuclock','8','--monitor','rgb']) as h:
 h.wait(9);base=h.basepage()['text'];a=lambda n:base+sym[n];r=Rdb()
 for mode in ['steady','tearing','automatic']:
  if mode=='steady':h.tap('A');h.wait(.3)
  elif mode=='tearing':h.tap('G');h.wait(.3)
  else:h.tap('G');h.tap('A');h.wait(.3)
  r.cmd('break',wait=1);r.cmd('profile 1');r.cmd('run');h.wait(8);r.cmd('break',wait=2)
  data=profile_lines(r.take('!profile'));assert data
  rows={pc:(n,c)for pc,n,c in data};frames=rows[a('Crt_FrameDone')][0];assert frames>50
  groups={}
  for name in ['Crt_Update','Crt_Render','Crt_ImageUpdate','Crt_MaskUpdate']:
   assert a(name)<a(name+'End'),name
   groups[name]=sum(c for pc,n,c in data if a(name)<=pc<a(name+'End'))
  groups['CrtRand']=sum(c for pc,n,c in data if a('CrtRand')<=pc<a('Crt_Update'))
  item={'mode':mode,'frames':frames,'cycles':groups,'cycles_per_frame':{k:round(v/frames,2)for k,v in groups.items()},'cycles_total_per_frame':round(sum(groups.values())/frames,2),'percent_160000_cycle_frame':round(sum(groups.values())/frames/1600,3)}
  out.append(item);print(json.dumps(item),flush=True)
  r.cmd('profile 0');r.cmd('run')
 r.s.close()
(root/'analysis/profile.json').write_text(json.dumps({'machine':'STE, 68000, 8 MHz, 1 MiB, RGB PAL, German TOS 1.62','method':'HRDB per-instruction cycle attribution. Includes C update/random generation, ASM wrapper, changed image blits and their shared-mode busy/restart wait, and dark-mask update. Excludes Screen_Update/VBL/input/OS wrappers; 160000 cycles per 50 Hz frame.','program_sha256':hashlib.sha256((root/'CRT.PRG').read_bytes()).hexdigest(),'windows':out},indent=2)+'\n')
