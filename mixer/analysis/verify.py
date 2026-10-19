"""Run production AMIXER refill/core on a native 68000 and check PCM bytes."""
from pathlib import Path
import os,sys,time,struct,re,json,hashlib
os.environ.setdefault('SDL_VIDEODRIVER','dummy');os.environ.setdefault('SDL_AUDIODRIVER','dummy')
sys.path.insert(0,str(Path.home()/'.agents/skills/hatari-debugging/scripts'))
from hatari_session import HatariSession,nm_symbols
root=Path(__file__).resolve().parents[3];out=Path(__file__).resolve().parent
prg=out/'AMIXDBG.PRG';symbols=nm_symbols(str(prg),nm='m68k-atari-mintelf-nm')
def array(name):
 s=(root/'godlib/audio'/name[0]).read_text();s=s[s.index(name[1]):];s=s[s.index('{'):s.index('}')]
 return [int(x,16)for x in re.findall(r'0x([0-9a-fA-F]+)',s)]
sine=array(('am_sine.h','gAudioMixerSineLaw'))
pl=array(('ampanlaw.h','gAudioMixerPanLawLeftTable'));pr=array(('ampanlaw.h','gAudioMixerPanLawRightTable'))
def gains(law,vol,pan):
 l,r=((255-pan,pan),(sine[pan],pan),(pl[pan],pr[pan]))[law]
 return (l*vol+127)//255,(r*vol+127)//255
def scale(x,g):return (abs(x)*g//255)*(-1 if x<0 else 1)
def pcm(seq,vol,pan,law=0):
 l,r=gains(law,vol,pan);return bytes(v&255 for x in seq for v in(scale(x,l),scale(x,r)))
with HatariSession(str(prg),tos=str(Path.home()/'Atari/tos/TOS v1.62 (1990)(Atari Corp)(STE)(De).img'),machine='ste',sound=True,debug_except='bus,address,illegal',extra_args=['--confirm-quit','false','--memsize','1','--cpuclock','8','--monitor','rgb'])as h:
 h.wait(25);base=h.basepage()['text'];a=lambda n:base+symbols[n]
 h.debug('b pc = $%x :once'%a('MixCheck_Marker'),settle=1)
 def dump(addr,size):
  path=out/'dump.bin';path.unlink(missing_ok=True);h.stdin_cmd('savebin %s $%x $%x'%(path,addr,size),settle=.02)
  for _ in range(300):
   if path.exists()and path.stat().st_size==size:return path.read_bytes()
   time.sleep(.01)
  raise AssertionError(('dump timeout',size,h.lines[-10:]))
 def word(n):return struct.unpack('>H',dump(a(n),2))[0]
 def pointer(n):return struct.unpack('>I',dump(a(n),4))[0]
 assert word('gMixReady')==1,(h.lines[-20:])
 assert word('gMixError')==0,word('gMixError')
 actual=dump(a('gMixOutput'),105*512);expected=b''
 for law in range(3):
  for vol in (0,1,64,127,128,254,255):
   for pan in(0,64,128,192,255):expected+=pcm(list(range(128))+list(range(-128,0)),vol,pan,law)
 assert actual==expected,next((i,u,v)for i,(u,v)in enumerate(zip(actual,expected))if u!=v)
 special=dump(a('gMixSpecial'),8*512);short=[127,-128,37]
 want=[pcm([127 if i%2==0 else -128 for i in range(256)],255,0),
       pcm([127,127,-128,-128,37,37]+[0]*250,255,255),
       pcm([short[(i//2)%3]for i in range(256)],255,0),
       pcm([short[((i+256)//2)%3]for i in range(256)],128,128),bytes(512),
       pcm([short[(i//4)%3]for i in range(256)],255,0)]
 for i,data in enumerate(want):assert special[i*512:(i+1)*512]==data,('special',i)
 low=dump(a('gMixLow'),8*512);values=list(range(128))+list(range(-128,0))
 lowwant=[pcm(values[::2]+[0]*128,255,0),pcm([short[(i*2)%3]for i in range(256)],255,255),
          pcm([short[(i//2)%3]for i in range(256)],255,0),pcm(values,255,128),pcm(values,128,192)]
 mixed=bytearray()
 for i in range(256):
  x=short[(i//2)%3];y=short[(i*2)%3];l0,r0=gains(0,200,32);l1,r1=gains(0,180,224)
  mixed.extend(v&255 for v in(scale(x,l0)+scale(y,l1),scale(x,r0)+scale(y,r1)))
 lowwant.append(bytes(mixed));lowwant.append(pcm([127]*256,255,0));lowwant.append(pcm(values[::2]+[0]*128,64,64))
 for i,data in enumerate(lowwant):assert low[i*512:(i+1)*512]==data,('low rate',i,next((j,u,v)for j,(u,v)in enumerate(zip(low[i*512:(i+1)*512],data))if u!=v))
 single=dump(a('gMixSingle'),1024)
 assert single[:512]==pcm([127,-128]*128,192,192)
 assert single[512:]==pcm([127,127,-128,-128]*64,192,192)
 pairs=dump(a('gMixPairs'),524288)
 sums=[max(-128,min(127,(x if x<128 else x-256)+(y if y<128 else y-256)))for x in range(256)for y in range(256)]
 pair_left=bytes(c for x in sums for c in (x&255,0));pair_right=bytes(c for x in sums for c in (0,x&255))
 safeleft=bytearray();safecentre=bytearray()
 for x in range(256):
  for y in range(256):
   xx=x if x<128 else x-256;yy=y if y<128 else y-256
   safeleft.extend(((scale(xx,128)+scale(yy,128))&255,0))
   safecentre.extend(((scale(xx,127)+scale(yy,127))&255,(scale(xx,128)+scale(yy,128))&255))
 assert pairs==pair_left+pair_right+safeleft+safecentre,'exhaustive saturation and carry-corrected packed mix'
 heartbeat=word('gMixHeartbeat');ring=pointer('gpAudioMixerBuffer')
 # Resume through multiple complete DMA ring wraps, then validate every stereo pair.
 h.stdin_cmd('c',settle=2)
 h.debug('b pc = $%x :once'%a('MixCheck_Marker'),settle=.5)
 delta=(word('gMixHeartbeat')-heartbeat)&65535;assert delta>=50,delta
 raw=dump(ring,8192)
 allowed=set()
 for x in (127,-128):
  for y in(127,-128):
   l0,r0=gains(0,180,32);l1,r1=gains(0,200,224)
   allowed.add(bytes(max(-128,min(127,v))&255 for v in(scale(x,l0)+scale(y,l1),scale(x,r0)+scale(y,r1))))
 assert all(raw[i:i+2]in allowed for i in range(0,8192,2)),('live ring',allowed,raw[:32])
 assert word('gMixError')==0
 # Trigger the real 25 -> 12.5 kHz switch, then check a complete low-rate ring.
 h.stdin_cmd('b pc = $%x :once'%a('MixCheck_Marker'),settle=.01)
 h.stdin_cmd('w $%x 0 1'%a('gMixLive'),settle=.01)
 h.stdin_cmd('c',settle=.3)
 assert word('gMixReady')==2 and word('gMixError')==0,(word('gMixReady'),word('gMixError'))
 lowstart=word('gMixHeartbeat');h.stdin_cmd('c',settle=2)
 h.debug('b pc = $%x :once'%a('MixCheck_Marker'),settle=.3)
 lowvbls=(word('gMixHeartbeat')-lowstart)&65535;assert lowvbls>=50,lowvbls
 raw=dump(ring,8192);l0,r0=gains(0,180,32);l1,r1=gains(0,200,224)
 pair=bytes(v&255 for v in(scale(127,l0)+scale(127,l1),scale(127,r0)+scale(127,r1)))
 assert raw==pair*4096,('low DMA ring',raw[:32],pair)
 assert dump(0xffff8921,1)[0]&3==1
 h.stdin_cmd('b pc = $%x :once'%a('MixCheck_Marker'),settle=.01)
 h.stdin_cmd('w $%x 0 1'%a('gMixLive'),settle=.01)
 h.stdin_cmd('c',settle=1)
 assert word('gMixExit')==1 and word('gMixError')==0,(word('gMixExit'),word('gMixError'))
 h.stdin_cmd('c',settle=.3)
 assert any('Program exit' in line for line in h.lines),h.lines[-10:]
 assert not any('CPU exception'in line or 'Address Error'in line or 'Bus Error'in line for line in h.lines),h.lines[-20:]
 report={'program_sha256':hashlib.sha256(prg.read_bytes()).hexdigest(),'machine':'STE, 68000, 8 MHz, 1 MiB, German TOS 1.62','gain_pan_law_cases':105,'exact_pcm_bytes_checked':len(expected)+13*512+524288+1024+512,'low_rate_conversion_cases':8,'exhaustive_two_voice_pairs':262144,'live_ring_bytes_checked':16384,'live_vbls':{'25033_Hz':delta,'12517_Hz':lowvbls},'tests':['all 256 signed PCM values','mute and unity endpoints','three pan laws','positive/negative clipping','odd source address and 3-byte length with nonzero guard','12.5/6.25 kHz duplication','split refill phase continuity','loops, live volume/pan, stop','invalid inputs rejected','legacy API slot allocation/stealing','DMA ring wraps','disable/deinit/reinit, natural one-shot completion','12.5 kHz unity, expansion, decimation, odd-length looping and mixed rates','invalid/same-rate/disabled switches','live DMA 25 -> 12.5 -> 25 kHz, queue reset','second voice alone: native, repetition and decimation','odd one-voice tails and 257-frame two-voice spans','all 65536 input pairs for L/R saturation and both safe packed paths','clean shutdown'],'result':'PASS'}
 (out/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
 (out/'dump.bin').unlink(missing_ok=True)
