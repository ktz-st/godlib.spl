"""Native VBL-counter cadence test, >=two complete rotations at default speed.
No profiler or breakpoints inside the measured interval.
"""
import os,sys,json,hashlib
from pathlib import Path
os.environ.setdefault('SDL_VIDEODRIVER','dummy');os.environ.setdefault('SDL_AUDIODRIVER','dummy')
sys.path.insert(0,str(Path.home()/'.agents/skills/hatari-debugging/scripts'))
from hatari_session import HatariSession,nm_symbols
root=Path(__file__).resolve().parents[1];sym=nm_symbols(str(root/'analysis/RTDBG.PRG'),nm='m68k-atari-mintelf-nm');results=[]
for machine in ('ste','st'):
 tos='TOS v1.62 (1990)(Atari Corp)(STE)(De).img'if machine=='ste'else 'TOS v2.06 (1991)(Atari Corp)(Mega-STE)(UK).img'
 with HatariSession(str(root/'WEDGERT.PRG'),tos=str(Path.home()/'Atari/tos'/tos),machine=machine,sound=False,extra_args=['--confirm-quit','false','--memsize','1','--cpuclock','8','--cpulevel','0','--monitor','rgb'])as h:
  h.wait(9);base=h.basepage()['text'];a=lambda n:base+sym[n]
  counters=['gWedgesFrames','gWedgesLastVbl','gWedgesMissedVbl'];lo=min(a(n)for n in counters);hi=max(a(n)for n in counters)+4
  def sample():
   m=h.mem(lo,hi-lo);return [m.u32(a(n))for n in counters]
  for direction in ('forward','reverse'):
   if direction=='reverse':h.tap('R',hold=.13,after=.3)
   f0,v0,m0=sample();h.wait(12);f1,v1,m1=sample()
   item={'machine':machine,'direction':direction,'TOS':tos,'frame_delta':f1-f0,'vbl_delta':v1-v0,'missed_vbl_delta':m1-m0,'nominal_updates_per_second':50*(f1-f0)/(v1-v0),'rotations_at_speed_6':(f1-f0)*6/1536}
   late=h.mem(a('gWedgesLate'),64)
   item['late_phases']={str(i):late.u16(a('gWedgesLate')+i*2)for i in range(32)if late.u16(a('gWedgesLate')+i*2)}
   print(item,flush=True)
   assert f1-f0>=512 and abs((f1-f0)-(v1-v0))<=1 and m1==m0,item
   assert not any(any(s in l for s in ['Bus Error','Address Error','Illegal instruction'])for l in h.lines)
   results.append(item)
(root/'analysis/cadence-live.json').write_text(json.dumps({'program_sha256':hashlib.sha256((root/'WEDGERT.PRG').read_bytes()).hexdigest(),'configuration':'68000, 8 MHz, 1 MiB, PAL RGB','method':'Uninterrupted normal-speed live rendering for 12 seconds between debugger snapshots of main-loop frame/VBL/missed-VBL counters. Both rotation directions: one update per VBL, >two full rotations per sample, no missed VBL permitted. No frame cache or blitter.','results':results},indent=2)+'\n')
print('PASS 50 Hz live cadence on ST and STE',flush=True)
