#!/usr/bin/env python3
"""Run native sequence oracle/lifecycle regression under German TOS 1.62."""
from pathlib import Path
import sys,os,time,tempfile,shutil,json,hashlib
os.environ.setdefault('SDL_VIDEODRIVER','dummy');os.environ.setdefault('SDL_AUDIODRIVER','dummy')
sys.path.insert(0,str(Path.home()/'.agents/skills/hatari-debugging/scripts'))
from hatari_session import HatariSession,nm_symbols
root=Path(__file__).resolve().parents[1];out=root/'analysis';sy=nm_symbols(str(out/'RJPCHECK.PRG'),nm='m68k-atari-mintelf-nm')
with tempfile.TemporaryDirectory(prefix='rjp-core-') as tmp:
 tmp=Path(tmp);run=tmp/'RJPCHECK.PRG';shutil.copy2(out/'RJPCHECK.PRG',run)
 for p in list(root.glob('*.SNG'))+list(root.glob('*.INS'))+[root.parent/'lancemod/LOSTPARO.MOD']:shutil.copy2(p,tmp/p.name)
 with HatariSession(str(run),hatari='/opt/homebrew/opt/hatari/Hatari.app/Contents/MacOS/hatari',tos=str(Path.home()/'Atari/tos/TOS v1.62 (1990)(Atari Corp)(STE)(De).img'),sound=False,screenshot_dir=str(out/'shots/check'),debug_except='bus,address,illegal',extra_args=['--confirm-quit','false','--memsize','1','--cpuclock','8','--monitor','rgb']) as h:
  h.wait(9);base=h.basepage()['text'];h.control('hatari-option -D',settle=.1)
  def data(name,size=2):
   path=tmp/'dump.bin';path.unlink(missing_ok=True);h.debug(f'savebin {path} ${base+sy[name]:x} ${size:x}',settle=.03)
   for _ in range(100):
    if path.exists()and path.stat().st_size==size:return path.read_bytes()
    time.sleep(.01)
   raise AssertionError(h.lines[-15:])
  def val(name,size=2):return int.from_bytes(data(name,size),'big')
  deadline=time.time()+150
  while not val('gTestDone') and time.time()<deadline:h.wait(.5)
  result={n:val(n,4 if n in ['gTestCompared','gTestTicks','gTestFreeBefore','gTestFreeAfter'] else 2) for n in ['gTestDone','gTestPass','gTestStage','gTestBank','gTestSong','gTestChannel','gTestWant','gTestGot','gTestCompared','gTestTicks','gTestFreeBefore','gTestFreeAfter']}
  result['resident_bytes']=[int.from_bytes(data('gTestResident',8)[i:i+4],'big') for i in [0,4]]
  result['result']='PASS' if result['gTestPass'] else 'FAIL'
  result['test_sha256']=hashlib.sha256(run.read_bytes()).hexdigest()
  result['checks']=str(result['gTestCompared'])+' sequencer ticks, note-trigger fixtures 21..24, all rates, USP/VBL, exclusive ownership, full RAM recovery, ProTracker restart'
  (out/'core-result.json').write_text(json.dumps(result,indent=2)+'\n');print(result,flush=True)
  if not result['gTestPass']:(out/'core-failure.log').write_text('\n'.join(h.lines));raise AssertionError(result)
  assert not any('cpu exception'in x.lower()for x in h.lines),h.lines[-20:]
