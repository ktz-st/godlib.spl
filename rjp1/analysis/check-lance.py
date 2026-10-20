#!/usr/bin/env python3
"""Existing LanceMod release after extraction of the shared Paula backend."""
from pathlib import Path
import os,sys,time,tempfile,shutil,json,hashlib,wave,array
os.environ.setdefault('SDL_VIDEODRIVER','dummy');os.environ.setdefault('SDL_AUDIODRIVER','dummy')
sys.path.insert(0,str(Path.home()/'.agents/skills/hatari-debugging/scripts'))
from hatari_session import HatariSession,nm_symbols
out=Path(__file__).resolve().parent;root=out.parent.parent/'lancemod';sy=nm_symbols(str(root/'analysis/LMDBG.PRG'),nm='m68k-atari-mintelf-nm')
with tempfile.TemporaryDirectory(prefix='rjp-lance-') as tmp:
 tmp=Path(tmp);run=tmp/'LANCEMOD.PRG';shutil.copy2(root/'LANCEMOD.PRG',run);shutil.copy2(root/'LOSTPARO.MOD',tmp/'LOSTPARO.MOD');wav=tmp/'audio.wav';cfg=tmp/'audio.cfg'
 cfg.write_text('[Sound]\nbEnableSound = TRUE\nnPlaybackFreq = 44100\nszYMCaptureFileName = '+str(wav)+'\n')
 with HatariSession(str(run),hatari='/opt/homebrew/opt/hatari/Hatari.app/Contents/MacOS/hatari',tos=str(Path.home()/'Atari/tos/TOS v1.62 (1990)(Atari Corp)(STE)(De).img'),sound=True,debug_except='bus,address,illegal',extra_args=['--configfile',str(cfg),'--sound','44100','--confirm-quit','false','--memsize','1','--cpuclock','8','--monitor','rgb'])as h:
  h.wait(9);base=h.basepage()['text'];h.control('hatari-option -D',settle=.1)
  def val(name):
   p=tmp/'dump.bin';p.unlink(missing_ok=True);h.debug(f'savebin {p} ${base+sy[name]:x} $2',settle=.15);return int.from_bytes(p.read_bytes(),'big')
  def key(scan):h.control(f'hatari-event keydown 0x{scan:02x}',settle=.15);h.control(f'hatari-event keyup 0x{scan:02x}',settle=.15)
  assert val('gLanceVisReady')==1
  h.control('hatari-shortcut recsound',settle=.1)
  for view in range(5):
   if view:key(24)
   h.wait(.5);assert val('gLanceVisMode')==view
  h.control('hatari-shortcut recsound',settle=.1)
  with wave.open(str(wav),'rb')as w:
   samples=array.array('h');samples.frombytes(w.readframes(w.getnframes()))
   peaks=[max(abs(v) for v in samples[i::2])for i in [0,1]];assert min(peaks)>100,peaks
  key(1);h.wait(.5);assert val('gLanceVisExited')==1 and h.basepage()['text']!=base
  assert not any('Bus error'in x or 'Address error'in x or 'Illegal instruction'in x for x in h.lines),h.lines[-30:]
 result={'result':'PASS','release_sha256':hashlib.sha256(run.read_bytes()).hexdigest(),'audio_channel_peaks':peaks,'views_checked':['bars','four scopes','XY','stereo','mono'],'exit':'returned to TOS'}
(out/'lance-regression.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
