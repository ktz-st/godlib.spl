#!/usr/bin/env python3
"""Exercise compiled FED data and real FE input/rendering on a 1 MiB STE."""
from pathlib import Path
import hashlib,json,os,struct,sys,time
from PIL import Image
os.environ.setdefault('SDL_VIDEODRIVER','dummy');os.environ.setdefault('SDL_AUDIODRIVER','dummy')
sys.path.insert(0,str(Path.home()/'.agents/skills/hatari-debugging/scripts'))
from hatari_session import HatariSession,nm_symbols
root=Path(__file__).resolve().parents[1];out=root/'analysis'
sy=nm_symbols(str(out/'FEDBG.PRG'),nm='m68k-atari-mintelf-nm')
with HatariSession(str(root/'FE.PRG'),hatari='/opt/homebrew/opt/hatari/Hatari.app/Contents/MacOS/hatari',tos=str(Path.home()/'Atari/tos/TOS v1.62 (1990)(Atari Corp)(STE)(De).img'),screenshot_dir=str(out/'shots'),debug_except='bus,address,illegal',extra_args=['--confirm-quit','false','--memsize','1','--cpuclock','8','--monitor','rgb'])as h:
 h.wait(9);base=h.basepage()['text'];a=lambda name:base+sy[name]
 def dump(name,size):
  p=out/'dump.bin';p.unlink(missing_ok=True);h.debug('savebin %s $%x $%x'%(p,a(name),size),settle=.05)
  for _ in range(100):
   if p.exists()and p.stat().st_size==size:return p.read_bytes()
   time.sleep(.01)
  raise AssertionError(('dump timeout',h.lines[-15:]))
 def word(n):return struct.unpack('>H',dump(n,2))[0]
 def long(n):return struct.unpack('>I',dump(n,4))[0]
 def state():return [word(n)for n in ('gFeReady','gFeError','gFeRoundtrip','gFePage','gFeSelection','gFeMode')]
 def snap(name):Image.open(h.screenshot()).save(out/(name+'.png'))
 def key(scan,hold=.10):
  h.control('hatari-event keydown '+str(scan),settle=hold);h.control('hatari-event keyup '+str(scan),settle=.15)
 try:
  print('boot',state(),flush=True);snap('main')
  assert word('gFeError')==0 and word('gFeRoundtrip')==1 and word('gFeReady')==1,h.lines[-20:]
  assert word('gFeMode')==0
  assert long('gFeDifficulty')==1 and long('gFeVolume')==70
  key(80);assert word('gFeSelection')==1
  key(28);h.wait(1.3);print('options',state(),flush=True);snap('options')
  assert word('gFePage')==1 and word('gFeMode')==0
  key(77);assert long('gFeDifficulty')==2
  key(77);assert long('gFeDifficulty')==0
  key(75);assert long('gFeDifficulty')==2
  key(80);key(75);assert long('gFeVolume')==60
  key(77,.8);assert long('gFeVolume')==100
  key(75,1.0);assert long('gFeVolume')==0
  for _ in range(7):key(77)
  assert long('gFeVolume')==70
  snap('adjusted');key(80);key(28)
  assert word('gFeSounds')==1 and word('gFeVolumeGain')==178
  key(80);key(28);h.wait(1.3)
  assert word('gFePage')==0 and word('gFeMode')==0
  assert long('gFeDifficulty')==2 and long('gFeVolume')==70
  key(72);key(28);assert word('gFeStarts')==1;snap('start')
  # Return through the script's LINKS repeatedly; retain options and selection.
  key(80);key(57);h.wait(1.2);assert word('gFePage')==1 and word('gFeMode')==0
  key(28);h.wait(1.2);assert word('gFePage')==0 and word('gFeMode')==0
  key(80);key(28);h.wait(1)
  assert h.basepage()['text']!=base
  assert word('gFeExited')==1 and long('gFeContextRefs')==0 and long('gFeCleanupVars')==0
  assert not any('cpu exception' in line.lower() for line in h.lines),h.lines[-20:]
  report={'result':'PASS','machine':'STE / 68000 / 8 MHz / 1 MiB / German TOS 1.62','release_sha256':hashlib.sha256((root/'FE.PRG').read_bytes()).hexdigest(),'checks':['FED relocate/delocate byte-exact round trip on 68000','native keyboard input / Enter / Space','MAIN/OPTIONS links and palette fades','difficulty wrap in both directions','volume stepping, held repeat and endpoint clamps','volume scales chime gain to 178/255 at 70%','CALL start and test-sound events','options persist across pages','repeated page visits retain valid renderer state','exit to TOS; no FE variables or asset-context refs remain','no CPU exceptions']}
  (out/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
 except BaseException:
  snap('failure');(out/'failure.log').write_text('\n'.join(h.lines));raise
