#!/usr/bin/env python3
"""Five minutes of WARX4 per output rate; virtual timer measured inside VBL."""
from pathlib import Path
import os,sys,time,tempfile,shutil,json,hashlib
os.environ.setdefault('SDL_VIDEODRIVER','dummy');os.environ.setdefault('SDL_AUDIODRIVER','dummy')
sys.path.insert(0,str(Path.home()/'.agents/skills/hatari-debugging/scripts'))
from hatari_session import HatariSession,nm_symbols
root=Path(__file__).resolve().parents[1];out=root/'analysis';sy=nm_symbols(str(out/'WARTIME.PRG'),nm='m68k-atari-mintelf-nm');result={}
with tempfile.TemporaryDirectory(prefix='rjp-war-timing-')as tmp:
 tmp=Path(tmp);run=tmp/'WARTIME.PRG';shutil.copy2(out/'WARTIME.PRG',run)
 for p in list(root.glob('*.SNG'))+list(root.glob('*.INS')):shutil.copy2(p,tmp/p.name)
 with HatariSession(str(run),hatari='/opt/homebrew/opt/hatari/Hatari.app/Contents/MacOS/hatari',tos=str(Path.home()/'Atari/tos/TOS v1.62 (1990)(Atari Corp)(STE)(De).img'),sound=False,debug_except='bus,address,illegal',extra_args=['--confirm-quit','false','--memsize','4','--cpuclock','8','--monitor','rgb'])as h:
  h.wait(9);base=h.basepage()['text'];h.control('hatari-option -D',settle=.1)
  def data(name,size=4):
   p=tmp/'dump.bin';p.unlink(missing_ok=True);h.debug(f'savebin {p} ${base+sy[name]:x} ${size:x}',settle=.08)
   for _ in range(100):
    if p.exists()and p.stat().st_size==size:return p.read_bytes()
    time.sleep(.01)
   raise AssertionError(h.lines[-25:])
  def val(name,size=4):return int.from_bytes(data(name,size),'big')
  def key(scan):h.control(f'hatari-event keydown 0x{scan:02x}',settle=.2);h.control(f'hatari-event keyup 0x{scan:02x}',settle=.2)
  key(50);deadline=time.time()+30
  while val('gRjpBank',2)!=1 and time.time()<deadline:h.wait(.1)
  h.wait(2)
  for rate in [2,1,3]:
   key(rate+1);h.wait(1);assert val('gRjpRate',2)==rate
   h.control('hatari-option --fast-forward true',settle=.1);deadline=time.time()+180
   while not val('gWarDone',2)and time.time()<deadline:h.wait(1)
   h.control('hatari-option --fast-forward false',settle=.1)
   assert val('gWarDone',2)==1,h.lines[-30:]
   def bins(name):b=data(name,64);return {str(i):int.from_bytes(b[i*2:i*2+2],'big')for i in range(32)if b[i*2:i*2+2]!=b'\0\0'}
   result[str(rate)]={n:val(n)for n in ['gWarTicks','gWarMaxGap','gWarMaxCost','gWarLongGaps','gWarOverruns']};result[str(rate)]['gap_bins_hz200']=bins('gWarGapBins');result[str(rate)]['cost_bins_hz200']=bins('gWarCostBins');print(rate,result[str(rate)],flush=True)
  key(1);h.wait(.5)
  (out/'war-timing.log').write_text('\n'.join(h.lines))
report={'machine':'STE 8 MHz PAL, 4 MiB, German TOS 1.62','song':'WARX4 subsong 1','method':'Instrumentation wraps actual release UI VBL callback. At least 15000 PAL callbacks per rate. Internal HZ200 timestamps, no debugger/disk operations in callback. Fast-forward changes host speed, not emulated CPU frequency. 5ms quantization; cost>=4 is conservatively flagged, gap>=6 is a discontinuity.','results':result,'test_sha256':hashlib.sha256((out/'WARTIME.PRG').read_bytes()).hexdigest()}
(out/'war-timing.json').write_text(json.dumps(report,indent=2)+'\n')
