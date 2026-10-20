#!/usr/bin/env python3
"""Actual release: two banks, two mixers, two rates, audio/VBL and UI switches."""
from pathlib import Path
import os,sys,time,tempfile,shutil,json,hashlib,wave,array,math,struct
from PIL import Image
os.environ.setdefault('SDL_VIDEODRIVER','dummy');os.environ.setdefault('SDL_AUDIODRIVER','dummy')
sys.path.insert(0,str(Path.home()/'.agents/skills/hatari-debugging/scripts'))
from hatari_session import HatariSession,nm_symbols
root=Path(__file__).resolve().parents[1];out=root/'analysis';sy=nm_symbols(str(out/'RJPDBG.PRG'),nm='m68k-atari-mintelf-nm');results={}
with tempfile.TemporaryDirectory(prefix='rjp-mixers-')as tmp:
 tmp=Path(tmp);run=tmp/'RJP1.PRG';shutil.copy2(root/'RJP1.PRG',run)
 for p in list(root.glob('*.SNG'))+list(root.glob('*.INS')):shutil.copy2(p,tmp/p.name)
 wav=tmp/'audio.wav';cfg=tmp/'audio.cfg';cfg.write_text('[Sound]\nbEnableSound = TRUE\nbEnableSoundSync = TRUE\nnPlaybackFreq = 50066\nszYMCaptureFileName = '+str(wav)+'\n')
 with HatariSession(str(run),hatari='/opt/homebrew/opt/hatari/Hatari.app/Contents/MacOS/hatari',tos=str(Path.home()/'Atari/tos/TOS v1.62 (1990)(Atari Corp)(STE)(De).img'),sound=True,screenshot_dir=str(out/'shots/mixers'),debug_except='bus,address,illegal',extra_args=['--configfile',str(cfg),'--sound','50066','--sound-sync','true','--sound-buffer-size','60','--confirm-quit','false','--memsize','4','--cpuclock','8','--monitor','rgb'])as h:
  h.wait(9);base=h.basepage()['text'];h.control('hatari-option -D',settle=.1)
  def data(name,size=2):
   p=tmp/'dump';p.unlink(missing_ok=True);h.debug(f'savebin {p} ${base+sy[name]:x} ${size:x}',settle=.05)
   for _ in range(100):
    if p.exists()and p.stat().st_size==size:return p.read_bytes()
    time.sleep(.01)
   raise AssertionError(h.lines[-30:])
  def val(name,size=2):return int.from_bytes(data(name,size),'big')
  def key(scan):h.control(f'hatari-event keydown 0x{scan:02x}',settle=.15);h.control(f'hatari-event keyup 0x{scan:02x}',settle=.15)
  def frames(n=3):
   before=val('gRjpFrames',4);deadline=time.time()+30
   while val('gRjpFrames',4)<before+n and time.time()<deadline:h.wait(.1)
   assert val('gRjpFrames',4)>=before+n,h.lines[-20:]
  try:
   deadline=time.time()+45
   while not val('gRjpReady') and time.time()<deadline:h.wait(.15)
   assert val('gRjpReady')==1
   for bank in range(2):
    if bank:key(50);frames()
    for mix in range(2):
     if val('gRjpMixer')!=mix:key(48);frames()
     assert val('gRjpMixer')==mix and val('gRjpBank')==bank
     for rate in [2,1]:
      key(rate+1);frames();assert val('gRjpRate')==rate
      before=val('gRjp1Ticks',4);vbl0=int.from_bytes(data('gRjpFrames',4),'big')
      h.control('hatari-shortcut recsound',settle=.1);h.wait(13);h.control('hatari-shortcut recsound',settle=.1)
      after=val('gRjp1Ticks',4);assert after-before>400
      with wave.open(str(wav),'rb')as w:
       samples=array.array('h');samples.frombytes(w.readframes(w.getnframes()))
       if sys.byteorder!='little':samples.byteswap()
       peaks=[max(abs(v)for v in samples[i::2])for i in [0,1]];rms=math.sqrt(sum(v*v for v in samples)/len(samples));assert min(peaks)>100 and rms>20,(bank,mix,rate,peaks,rms)
      info=struct.unpack('>4I4H',data('info',24));name=f'{["JON","WARX4"][bank]}-{["Lance","Leonard"][mix]}-{rate}'
      results[name]={'resident_song_bytes':info[1],'source_bytes':info[0],'mixer':info[-1],'channel_peaks':peaks,'rms':round(rms,2),'audio_ticks_during_capture':after-before}
      print(name,results[name],flush=True)
      if mix==1 and rate==2:Image.open(h.screenshot()).save(out/f'{["jon","war"][bank]}-leonard.png')
     # All advertised subsong slots, including silent slots, must remain responsive.
     for _ in range(info[4]):key(49);frames(1)
     key(59);frames();key(59)
   key(1);h.wait(.5);assert val('gRjpExited')==1 and h.basepage()['text']!=base
   assert not any('Bus error'in x or 'Address Error'in x or 'Illegal instruction'in x for x in h.lines),h.lines[-30:]
  except BaseException:
   (out/'mixers-failure.log').write_text('\n'.join(h.lines));Image.open(h.screenshot()).save(out/'mixers-failure.png');raise
report={'result':'PASS','release_sha256':hashlib.sha256((root/'RJP1.PRG').read_bytes()).hexdigest(),'machine':'STE 68000 8MHz PAL 4MiB German TOS 1.62','cases':results,'limits':'Actual stereo WAV signal checks, not subjective listening; independent native regression verifies exact VBL cadence and cleanup.'}
(out/'verification-mixers.json').write_text(json.dumps(report,indent=2)+'\n')
