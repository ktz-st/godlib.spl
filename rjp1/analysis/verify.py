#!/usr/bin/env python3
"""Release smoke test, all banks/rates, real stereo WAV and clean TOS exit."""
from pathlib import Path
import os,sys,time,tempfile,shutil,json,hashlib,wave,array,math
from PIL import Image
os.environ.setdefault('SDL_VIDEODRIVER','dummy');os.environ.setdefault('SDL_AUDIODRIVER','dummy')
sys.path.insert(0,str(Path.home()/'.agents/skills/hatari-debugging/scripts'))
from hatari_session import HatariSession,nm_symbols
root=Path(__file__).resolve().parents[1];out=root/'analysis'
hatari='/opt/homebrew/opt/hatari/Hatari.app/Contents/MacOS/hatari';tos=str(Path.home()/'Atari/tos/TOS v1.62 (1990)(Atari Corp)(STE)(De).img')
results={}
with tempfile.TemporaryDirectory(prefix='godlib-rjp1-') as tmp:
 folder=Path(tmp);run=folder/'RJP1.PRG';shutil.copy2(root/'RJP1.PRG',run)
 for p in list(root.glob('*.SNG'))+list(root.glob('*.INS')):shutil.copy2(p,folder/p.name)
 sy=nm_symbols(str(out/'RJPDBG.PRG'),nm='m68k-atari-mintelf-nm');wav=folder/'audio.wav';cfg=folder/'sound.cfg'
 cfg.write_text('[Sound]\nbEnableSound = TRUE\nbEnableSoundSync = FALSE\nnPlaybackFreq = 44100\nszYMCaptureFileName = '+str(wav)+'\n')
 with HatariSession(str(run),hatari=hatari,tos=tos,sound=True,screenshot_dir=str(out/'shots'),debug_except='bus,address,illegal',extra_args=['--configfile',str(cfg),'--sound','44100','--confirm-quit','false','--memsize','1','--cpuclock','8','--monitor','rgb']) as h:
  h.wait(9);base=h.basepage()['text'];h.control('hatari-option -D',settle=.1)
  def data(name,size=2):
   p=folder/'dump.bin';p.unlink(missing_ok=True);h.debug(f'savebin {p} ${base+sy[name]:x} ${size:x}',settle=.03)
   for _ in range(100):
    if p.exists() and p.stat().st_size==size:return p.read_bytes()
    time.sleep(.01)
   raise AssertionError(h.lines[-20:])
  def val(name,size=2):return int.from_bytes(data(name,size),'big')
  def key(scan):h.control(f'hatari-event keydown 0x{scan:02x}',settle=.12);h.control(f'hatari-event keyup 0x{scan:02x}',settle=.12)
  def frames(count=3):
   before=val('gRjpFrames',4);deadline=time.time()+30
   while val('gRjpFrames',4)<before+count and time.time()<deadline:h.wait(.1)
   assert val('gRjpFrames',4)>=before+count
  try:
   deadline=time.time()+35
   while not val('gRjpReady') and time.time()<deadline:h.wait(.2)
   assert val('gRjpReady')==1,h.lines[-20:]
   for bank in range(2):
    if bank:key(50);frames()
    assert val('gRjpBank')==bank
    for rate in [2,1,3]:
     key(rate+1);frames();assert val('gRjpRate')==rate
     h.control('hatari-shortcut recsound',settle=.2);h.wait(12);h.control('hatari-shortcut recsound',settle=.2)
     with wave.open(str(wav),'rb') as w:
      raw=w.readframes(w.getnframes());samples=array.array('h');samples.frombytes(raw)
      if sys.byteorder!='little':samples.byteswap()
      peaks=[max(abs(v) for v in samples[i::2]) for i in [0,1]];rms=math.sqrt(sum(v*v for v in samples)/len(samples))
      assert min(peaks)>100 and rms>20,(bank,rate,peaks,rms)
      results[f'{bank}-{rate}']={'channel_peaks':peaks,'rms':round(rms,2),'frames':val('gRjpFrames',4)}
     if bank==0 and rate==2:Image.open(h.screenshot()).save(out/'preview.png')
    for _ in range(8):key(49);frames()
    key(59);assert val('gRjpRaster')==1;key(59)
   key(1);h.wait(.5);assert val('gRjpExited')==1 and h.basepage()['text']!=base
   assert not any('cpu exception' in x.lower() for x in h.lines),h.lines[-20:]
  except BaseException:
   h.debug('r',settle=.1);h.debug('d pc',settle=.1);Image.open(h.screenshot()).save(out/'failure.png');(out/'failure.log').write_text('\n'.join(h.lines));raise
report={'result':'PASS','machine':'STE, 68000, 8 MHz, 1 MiB, PAL, German TOS 1.62','release_sha256':hashlib.sha256(run.read_bytes()).hexdigest() if run.exists() else hashlib.sha256((root/'RJP1.PRG').read_bytes()).hexdigest(),'cases':results,'limits':'Non-silent stereo recording and emulator smoke test; not subjective listening or real hardware certification.'}
(out/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
