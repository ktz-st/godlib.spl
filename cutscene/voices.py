"""Offline macOS speech -> signed 8-bit mono PCM for AMIXER (no cloud service)."""
from pathlib import Path
import subprocess,tempfile,struct,wave,re,json,hashlib
r=Path(__file__).resolve().parent
pages=re.findall(r'<PAGE NAME="([^"]+)">\s*\{(.*?)\}',(r/'scene.txt').read_text(),re.S)
manifest=[];preview=bytearray()
with tempfile.TemporaryDirectory(prefix='cutscene-voice-')as tmp:
 for name,text in pages:
  text=' '.join(text.split()).capitalize();aiff=Path(tmp)/(name+'.aiff');wav=Path(tmp)/(name+'.wav')
  subprocess.run(['say','-v','Daniel','-r','145','-o',str(aiff),text],check=True)
  subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(aiff),'-af','silenceremove=start_periods=1:start_duration=0.02:start_threshold=-50dB','-ar','12517','-ac','1','-c:a','pcm_s16le',str(wav)],check=True)
  with wave.open(str(wav),'rb')as f:
   assert f.getframerate()==12517 and f.getnchannels()==1
   data=f.readframes(f.getnframes());values=struct.unpack('<%dh'%(len(data)//2),data)
  peak=max(map(abs,values));assert peak>100 and len(values)>12517
  samples=[max(-124,min(124,round(x*124/peak)))for x in values]
  # Short ramps remove DC steps at speech clip boundaries.
  for i in range(min(64,len(samples)//2)):
   samples[i]=round(samples[i]*i/64);samples[-i-1]=round(samples[-i-1]*i/64)
  raw=bytes(x&255 for x in samples);(r/'assets'/(name+'.RAW')).write_bytes(raw)
  with wave.open(str(r/'assets'/(name+'.wav')),'wb')as f:
   f.setparams((1,2,12517,0,'NONE','not compressed'));f.writeframes(b''.join(struct.pack('<h',x*256)for x in samples))
  preview+=b''.join(struct.pack('<h',x*256)for x in samples)+bytes((12517//2)*2)
  manifest.append({'name':name,'text':text,'voice':'macOS Daniel (en_GB)','words_per_minute':145,'format':'signed 8-bit mono PCM','sample_rate':12517,'bytes':len(raw),'duration_seconds':len(raw)/12517,'sha256':hashlib.sha256(raw).hexdigest()})
with wave.open(str(r/'assets/narration.wav'),'wb')as f:
 f.setparams((1,2,12517,0,'NONE','not compressed'));f.writeframes(preview)
(r/'assets/voices.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(manifest,indent=2))
