#!/usr/bin/env python3
"""Long release WARX4 recording, with no debugger operations during capture."""
from pathlib import Path
import os,sys,tempfile,shutil,json,wave,array,math,hashlib,time
os.environ.setdefault('SDL_VIDEODRIVER','dummy');os.environ.setdefault('SDL_AUDIODRIVER','dummy')
sys.path.insert(0,str(Path.home()/'.agents/skills/hatari-debugging/scripts'))
from hatari_session import HatariSession,nm_symbols
root=Path(__file__).resolve().parents[1];out=root/'analysis';sy=nm_symbols(str(out/'RJPDBG.PRG'),nm='m68k-atari-mintelf-nm')
with tempfile.TemporaryDirectory(prefix='war-audio-')as tmp:
 tmp=Path(tmp);run=tmp/'RJP1.PRG';shutil.copy2(root/'RJP1.PRG',run)
 for p in list(root.glob('*.SNG'))+list(root.glob('*.INS')):shutil.copy2(p,tmp/p.name)
 wav=tmp/'war.wav';cfg=tmp/'audio.cfg';cfg.write_text('[Sound]\nbEnableSound = TRUE\nbEnableSoundSync = TRUE\nnPlaybackFreq = 50066\nszYMCaptureFileName = '+str(wav)+'\n')
 with HatariSession(str(run),hatari='/opt/homebrew/opt/hatari/Hatari.app/Contents/MacOS/hatari',tos=str(Path.home()/'Atari/tos/TOS v1.62 (1990)(Atari Corp)(STE)(De).img'),sound=True,debug_except='bus,address,illegal',extra_args=['--configfile',str(cfg),'--sound','50066','--sound-sync','true','--sound-buffer-size','60','--confirm-quit','false','--memsize','4','--cpuclock','8','--monitor','rgb'])as h:
  h.wait(9);base=h.basepage()['text'];h.control('hatari-option -D',settle=.1)
  h.control('hatari-event keydown 0x32',settle=.2);h.control('hatari-event keyup 0x32',settle=.2);h.wait(3)
  def value(n):
   p=tmp/'dump';p.unlink(missing_ok=True);h.debug(f'savebin {p} ${base+sy[n]:x} $2',settle=.2);return int.from_bytes(p.read_bytes(),'big')
  assert value('gRjpBank')==1 and value('gRjpRate')==2
  h.control('hatari-shortcut recsound',settle=.2);start=time.monotonic();h.wait(40);print('WAR capture 40s',flush=True);h.wait(40);h.control('hatari-shortcut recsound',settle=.2);wall=time.monotonic()-start
  assert h.basepage()['text']==base
  log='\n'.join(h.lines);(out/'war-audio.log').write_text(log)
  h.control('hatari-event keydown 0x01',settle=.2);h.control('hatari-event keyup 0x01',settle=.2)
 with wave.open(str(wav),'rb')as w:
  rate=w.getframerate();frames=w.getnframes();samples=array.array('h');samples.frombytes(w.readframes(frames))
 if sys.byteorder!='little':samples.byteswap()
 # Per-second amplitude to identify sustained digital silence / dropouts.
 seconds=[]
 for j in range(frames//rate):
  chunk=samples[j*rate*2:(j+1)*rate*2];seconds.append({'second':j,'peak':max(abs(x)for x in chunk),'rms':round(math.sqrt(sum(x*x for x in chunk)/len(chunk)),2)})
 holds=[];start=0
 for j in range(1,frames):
  if samples[2*j]!=samples[2*(j-1)] or samples[2*j+1]!=samples[2*(j-1)+1]:
   count=j-start
   if count>=rate//500 and max(abs(samples[2*start]),abs(samples[2*start+1]))>100:holds.append({'at_seconds':round(start/rate,4),'duration_ms':round(1000*count/rate,3),'left':samples[2*start],'right':samples[2*start+1]})
   start=j
 result={'result':'PASS' ,'release_sha256':hashlib.sha256(run.read_bytes()).hexdigest(),'rate':rate,'frames':frames,'recorded_seconds':frames/rate,'wall_seconds':wall,'channel_peaks':[max(abs(x)for x in samples[i::2])for i in [0,1]],'seconds':seconds,'constant_nonzero_stereo_holds_over_2ms':sorted(holds,key=lambda x:x['duration_ms'],reverse=True)[:20],'host_audio_warnings':[x for x in log.splitlines()if 'too slow'in x or 'sound samples'in x],'limits':'WAV signal/timing test, not subjective listening. Digital silence can be part of the song.'}
 # Keep a convenient short listening excerpt outside the repository.
 with wave.open('/tmp/WARX4-25K.wav','wb')as w:w.setnchannels(2);w.setsampwidth(2);w.setframerate(rate);w.writeframes(samples[rate*2*15:rate*2*45].tobytes())
(out/'war-audio.json').write_text(json.dumps(result,indent=2)+'\n');print({k:v for k,v in result.items()if k!='seconds'},flush=True)
