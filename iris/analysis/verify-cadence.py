"""Native VBL-counter cadence test, >=two complete rotations at default speed.
No profiler or breakpoints inside the measured interval.
"""
import os,sys,json,hashlib
from pathlib import Path
os.environ.setdefault('SDL_VIDEODRIVER','dummy');os.environ.setdefault('SDL_AUDIODRIVER','dummy')
sys.path.insert(0,str(Path.home()/'.agents/skills/hatari-debugging/scripts'))
from hatari_session import HatariSession,nm_symbols
root=Path(__file__).resolve().parents[1];sym=nm_symbols(str(root/'analysis/IRISDBG.PRG'),nm='m68k-atari-mintelf-nm');results=[]
for machine in ('ste','st'):
 tos='TOS v1.62 (1990)(Atari Corp)(STE)(De).img'if machine=='ste'else 'TOS v2.06 (1991)(Atari Corp)(Mega-STE)(UK).img'
 with HatariSession(str(root/'IRIS.PRG'),tos=str(Path.home()/'Atari/tos'/tos),machine=machine,sound=False,extra_args=['--confirm-quit','false','--memsize','1','--cpuclock','8','--cpulevel','0','--monitor','rgb'])as h:
  h.wait(9);base=h.basepage()['text'];a=lambda n:base+sym[n]
  counters=['gIrisFrames','gIrisLastVbl','gIrisMissedVbl','gIrisActiveFrames','gIrisActiveVbls'];lo=min(a(n)for n in counters);hi=max(a(n)for n in counters)+4
  def sample():
   m=h.mem(lo,hi-lo);return [m.u32(a(n))for n in counters]
  h.tap('A',hold=.15,after=.3)
  for direction in ('transition',):
   f0,v0,m0,af0,av0=sample();h.wait(14);f1,v1,m1,af1,av1=sample()
   item={'machine':machine,'direction':direction,'TOS':tos,'frame_delta':f1-f0,'vbl_delta':v1-v0,'missed_vbl_delta':m1-m0,'nominal_updates_per_second':50*(f1-f0)/(v1-v0),'transitions_sampled':True}
   late=h.mem(a('gIrisLate'),164)
   item['late_steps']={str((i//41+1,i%41)):late.u16(a('gIrisLate')+i*2)for i in range(82)if late.u16(a('gIrisLate')+i*2)}
   item.update(active_frame_delta=af1-af0,active_vbl_delta=av1-av0,active_updates_per_second=50*(af1-af0)/(av1-av0),achieved_50hz=(m1==m0 and abs((f1-f0)-(v1-v0))<=1))
   print(item,flush=True)
   assert f1-f0>=512 and af1-af0>=82 and av1>av0,item
   assert not any(any(s in l for s in ['Bus Error','Address Error','Illegal instruction'])for l in h.lines)
   results.append(item)
(root/'analysis/cadence.json').write_text(json.dumps({'program_sha256':hashlib.sha256((root/'IRIS.PRG').read_bytes()).hexdigest(),'configuration':'68000, 8 MHz, 1 MiB, PAL RGB','method':'Uninterrupted automatic iris transitions for 14 seconds between debugger snapshots. Reports both whole-loop and transition-only cadence; idle holds are excluded from active_updates_per_second. No frame cache. 50 Hz is a measured target, not an assertion.','results':results},indent=2)+'\n')
print('Cadence recorded. 50 Hz achieved:',all(i['achieved_50hz']for i in results),flush=True)
