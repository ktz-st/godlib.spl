#!/usr/bin/env python3
"""PAL VBL audio/USP regression and both release-rate visualization smoke tests."""
from pathlib import Path
import os,sys,time,tempfile,shutil,json,hashlib,wave,array,math
from PIL import Image
os.environ.setdefault('SDL_VIDEODRIVER','dummy');os.environ.setdefault('SDL_AUDIODRIVER','dummy')
sys.path.insert(0,str(Path.home()/'.agents/skills/hatari-debugging/scripts'))
from hatari_session import HatariSession,nm_symbols
root=Path(__file__).resolve().parents[1];out=root/'analysis'
hatari='/opt/homebrew/opt/hatari/Hatari.app/Contents/MacOS/hatari';tos=str(Path.home()/'Atari/tos/TOS v1.62 (1990)(Atari Corp)(STE)(De).img')
results={}
with tempfile.TemporaryDirectory(prefix='godlib-leonard-vbl-') as tmp:
 tmp=Path(tmp)
 cases=[('core',out/'LEOCHECK.PRG',out/'LEOCHECK.PRG'),('25k',root/'LEONARD.PRG',out/'LEODBG.PRG'),('12k',root/'LEO12.PRG',out/'LEO12DBG.PRG')]
 for mode,exe,sym in cases:
  folder=tmp/mode;folder.mkdir();run=folder/exe.name;shutil.copy2(exe,run);shutil.copy2(root/'LOSTPARO.MOD',folder/'LOSTPARO.MOD')
  sy=nm_symbols(str(sym),nm='m68k-atari-mintelf-nm');wav=folder/'audio.wav';cfg=folder/'sound.cfg'
  cfg.write_text('[Sound]\nbEnableSound = TRUE\nbEnableSoundSync = FALSE\nnPlaybackFreq = 44100\nszYMCaptureFileName = '+str(wav)+'\n')
  with HatariSession(str(run),hatari=hatari,tos=tos,sound=True,screenshot_dir=str(out/'shots'/mode),debug_except='bus,address,illegal',extra_args=['--configfile',str(cfg),'--sound','44100','--confirm-quit','false','--memsize','1','--cpuclock','8','--monitor','rgb']) as h:
   h.wait(9);base=h.basepage()['text']
   def data_at(addr,size):
    p=out/'temp-dump.bin';p.unlink(missing_ok=True);h.debug(f'savebin {p} ${addr:x} ${size:x}',settle=.05)
    for _ in range(100):
     if p.exists()and p.stat().st_size==size:return p.read_bytes()
     time.sleep(.01)
    raise AssertionError(h.lines[-15:])
   def data(name,size):return data_at(base+sy[name],size)
   def val(name,size=2):return int.from_bytes(data(name,size),'big')
   def pair(name):b=data(name,8);return [int.from_bytes(b[i:i+4],'big')for i in [0,4]]
   def key(scan):h.control(f'hatari-event keydown 0x{scan:02x}',settle=.15);h.control(f'hatari-event keyup 0x{scan:02x}',settle=.15)
   def frames(count=3):
    first=val('gLeonardVisFrames',4);deadline=time.time()+8
    while val('gLeonardVisFrames',4)<first+count and time.time()<deadline:h.wait(.05)
    assert val('gLeonardVisFrames',4)>=first+count
   def snap(name):Image.open(h.screenshot()).save(out/(name+'.png'))
   try:
    ready='gLeoTestDone' if mode=='core' else 'gLeonardVisReady';deadline=time.time()+45
    while not val(ready)and time.time()<deadline:h.wait(.15)
    assert val(ready)==1,(mode,'not ready',h.lines[-20:])
    if mode=='core':
     assert val('gLeoTestPass')==1,('stage',val('gLeoTestStage'),h.lines[-20:])
     assert val('gLeoTestStage')==18 and val('gLeoBadMask')==0
     results[mode]={'result':'PASS','checks':18,'foreground_hold_audio_ticks':pair('gLeoHoldTicks'),'foreground_hold_pal_vbls':pair('gLeoHoldVbls'),'pcm_nonzero_bytes':pair('gLeoPcmNonzero'),'changing_pcm_windows':pair('gLeoPcmChanges'),'USP_sentinel':'0x12345678 preserved while foreground performs no rendering/ticks','cleanup':'callback count, trap #0, DMA off, workspace and free RAM restored at both rates'}
     snap('core');key(1);h.wait(.4);assert h.basepage()['text']!=base
    else:
     assert val('gLeonardVisAudioAttached')==1
     h.control('hatari-shortcut recsound',settle=.2)
     for view in range(5):
      if view:key(24) # O
      frames();assert val('gLeonardVisMode')==view
      before=val('gLeonardVisAudioTicks',4);frames(4)
      assert val('gLeonardVisAudioTicks',4)>before
      snap(mode+'-'+['bars','scopes','xy','stereo','mono'][view])
     key(47);frames();assert val('gLeonardVisEnabled')==0
     before=val('gLeonardVisAudioTicks',4);frames(4);assert val('gLeonardVisAudioTicks',4)>before
     key(47);frames();assert val('gLeonardVisEnabled')==1
     key(59);assert val('gLeonardVisRaster')==1;frames();key(59);assert val('gLeonardVisRaster')==0
     h.control('hatari-shortcut recsound',settle=.2)
     with wave.open(str(wav),'rb') as w:
      assert w.getsampwidth()==2 and w.getnchannels()==2
      raw=w.readframes(w.getnframes());samples=array.array('h');samples.frombytes(raw)
      if sys.byteorder!='little':samples.byteswap()
      peak=max(abs(v)for v in samples);rms=math.sqrt(sum(v*v for v in samples)/len(samples));channels=[max(abs(v)for v in samples[i::2])for i in [0,1]]
      assert peak>100 and min(channels)>100 and rms>20
      audio={'frames':w.getnframes(),'rate':w.getframerate(),'peak':peak,'rms':round(rms,2),'channel_peaks':channels}
     ticks=val('gLeonardVisAudioTicks',4);draws=val('gLeonardVisFrames',4)
     key(1);h.wait(.5);assert val('gLeonardVisExited')==1 and val('gLeonardVisAudioAttached')==0 and val('gLeonardVisAudioDetached')==1
     stopped=val('gLeonardVisAudioTicks',4);h.wait(.3);assert val('gLeonardVisAudioTicks',4)==stopped and h.basepage()['text']!=base
     results[mode]={'result':'PASS','release_sha256':hashlib.sha256(exe.read_bytes()).hexdigest(),'views':['bars','four scopes','ICE XY','stereo L/R','mono'],'audio_ticks':ticks,'rendered_frames':draws,'wav':audio,'cleanup':'VBL detached before shutdown; ticks stop and return to TOS'}
    assert not any('cpu exception'in line.lower()for line in h.lines),h.lines[-20:]
    print(mode,results[mode],flush=True)
   except BaseException:
    snap('failure-'+mode);(out/('failure-'+mode+'.log')).write_text('\n'.join(h.lines));raise
report={'result':'PASS','machine':'STE / 68000 / 8 MHz / 1 MiB / German TOS 1.62 / PAL','module_sha256':hashlib.sha256((root/'LOSTPARO.MOD').read_bytes()).hexdigest(),'cases':results,'limits':'Functional emulation and non-silent stereo WAV checks; not subjective listening, hardware certification or CPU profiling.'}
(out/'verification-vbl.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
