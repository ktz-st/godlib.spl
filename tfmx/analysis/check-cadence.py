#!/usr/bin/env python3
from pathlib import Path
import os,sys,time,tempfile,shutil,json,hashlib
os.environ.setdefault('SDL_VIDEODRIVER','dummy');os.environ.setdefault('SDL_AUDIODRIVER','dummy')
sys.path.insert(0,str(Path.home()/'.agents/skills/hatari-debugging/scripts'))
from hatari_session import HatariSession,nm_symbols
root=Path(__file__).resolve().parents[1];out=root/'analysis';sy=nm_symbols(str(out/'TFMCAD.PRG'),nm='m68k-atari-mintelf-nm')
with tempfile.TemporaryDirectory(prefix='tfmx-mixer-core-')as tmp:
 tmp=Path(tmp);run=tmp/'TFMCAD.PRG';shutil.copy2(out/'TFMCAD.PRG',run)
 for p in list(root.glob('*.MDT'))+list(root.glob('*.SMP')):shutil.copy2(p,tmp/p.name)
 with HatariSession(str(run),hatari='/opt/homebrew/opt/hatari/Hatari.app/Contents/MacOS/hatari',tos=str(Path.home()/'Atari/tos/TOS v1.62 (1990)(Atari Corp)(STE)(De).img'),sound=True,debug_except='bus,address,illegal',extra_args=['--confirm-quit','false','--fast-forward','false','--sound','50066','--sound-sync','true','--sound-buffer-size','60','--memsize','4','--cpuclock','8','--monitor','rgb'])as h:
  h.wait(9);base=h.basepage()['text'];h.control('hatari-option -D',settle=.1)
  def data(n,size=2):
   p=tmp/'dump';p.unlink(missing_ok=True);h.debug(f'savebin {p} ${base+sy[n]:x} ${size:x}',settle=.08)
   for _ in range(100):
    if p.exists()and p.stat().st_size==size:return p.read_bytes()
    time.sleep(.01)
   raise AssertionError(h.lines[-30:])
  def val(n,size=2):return int.from_bytes(data(n,size),'big')
  deadline=time.time()+120
  while not val('gDone') and time.time()<deadline:h.wait(.3)
  result={n:val(n)for n in ['gDone','gPass','gCase','gVideoMode','gVideoSync']}
  for n in ['gCadVbl','gSeq','gMix','gSkippedSeq']:
   raw=data(n,8);result[n]=[int.from_bytes(raw[i:i+4],'big')for i in range(0,8,4)]
  result['mode']='realtime sound-sync, 50066 Hz, STE PAL German TOS 1.62'
  result['result']='PASS'if result['gPass'] else'FAIL';result['test_sha256']=hashlib.sha256(run.read_bytes()).hexdigest()
  (out/'cadence-result.json').write_text(json.dumps(result,indent=2)+'\n');print(result,flush=True)
  if result['result']!='PASS':(out/'cadence-failure.log').write_text('\n'.join(h.lines));raise AssertionError(result)
