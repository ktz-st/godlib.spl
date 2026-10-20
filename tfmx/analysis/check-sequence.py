#!/usr/bin/env python3
from pathlib import Path
import os,sys,time,tempfile,shutil,json,hashlib
os.environ.setdefault('SDL_VIDEODRIVER','dummy');os.environ.setdefault('SDL_AUDIODRIVER','dummy')
sys.path.insert(0,str(Path.home()/'.agents/skills/hatari-debugging/scripts'))
from hatari_session import HatariSession,nm_symbols
root=Path(__file__).resolve().parents[1];out=root/'analysis';sy=nm_symbols(str(out/'TFMSEQ.PRG'),nm='m68k-atari-mintelf-nm')
with tempfile.TemporaryDirectory(prefix='tfmx-mixer-core-')as tmp:
 tmp=Path(tmp);run=tmp/'TFMSEQ.PRG';shutil.copy2(out/'TFMSEQ.PRG',run)
 for p in list(root.glob('*.MDT'))+list(root.glob('*.SMP')):shutil.copy2(p,tmp/p.name)
 with HatariSession(str(run),hatari='/opt/homebrew/opt/hatari/Hatari.app/Contents/MacOS/hatari',tos=str(Path.home()/'Atari/tos/TOS v1.62 (1990)(Atari Corp)(STE)(De).img'),sound=False,debug_except='bus,address,illegal',extra_args=['--confirm-quit','false','--fast-forward','true','--memsize','4','--cpuclock','8','--monitor','rgb'])as h:
  h.wait(9);base=h.basepage()['text'];h.control('hatari-option -D',settle=.1)
  def data(n,size=2):
   p=tmp/'dump';p.unlink(missing_ok=True);h.debug(f'savebin {p} ${base+sy[n]:x} ${size:x}',settle=.08)
   for _ in range(100):
    if p.exists()and p.stat().st_size==size:return p.read_bytes()
    time.sleep(.01)
   raise AssertionError(h.lines[-30:])
  def val(n,size=2):return int.from_bytes(data(n,size),'big')
  deadline=time.time()+70
  while not val('gSequenceDone') and time.time()<deadline:h.wait(.3)
  result={n:val(n)for n in ['gSequenceDone','gSequencePass','gSequenceSong','gSequenceField']}
  for n in ['gSequenceSteps','gSequenceExpected','gSequenceActual']:result[n]=val(n,4)
  for name,size in [('gPeriodMin',2),('gPeriodMax',2),('gPeriodOutside',4),('gVolumeMax',2),('gVolumeOutside',4)]:
   buf=data(name,7*size);result[name]=[int.from_bytes(buf[i:i+size],'big')for i in range(0,7*size,size)]
  result['result']='PASS'if result['gSequencePass']else'FAIL';result['test_sha256']=hashlib.sha256(run.read_bytes()).hexdigest()
  (out/'sequence-result.json').write_text(json.dumps(result,indent=2)+'\n');print(result,flush=True)
  if not result['gSequencePass']:(out/'sequence-failure.log').write_text('\n'.join(h.lines));raise AssertionError(result)
