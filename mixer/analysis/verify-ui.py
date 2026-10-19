"""Exercise the release binary, comparing both complete display pages to an oracle."""
from pathlib import Path
import os,sys,struct,time,json,hashlib
from PIL import Image
os.environ.setdefault('SDL_VIDEODRIVER','dummy');os.environ.setdefault('SDL_AUDIODRIVER','dummy')
sys.path.insert(0,str(Path.home()/'.agents/skills/hatari-debugging/scripts'))
from hatari_session import HatariSession,nm_symbols
r=Path(__file__).resolve().parents[1];out=r/'analysis'
sy=nm_symbols(str(out/'AMIXUI.PRG'),nm='m68k-atari-mintelf-nm')
release=r/'MIXER.TOS';debug=(out/'AMIXUI.PRG').read_bytes();binary=release.read_bytes()
# The first 128 startup bytes contain symbol-size metadata adjusted by strip.
# Remaining executable text/data and all runtime symbol offsets are identical.
size=sum(struct.unpack_from('>2I',binary,2));assert binary[28+128:28+size]==debug[28+128:28+size]
font=debug[28+sy['gFont8x8']:28+sy['gFont8x8']+12544]
def expected(volume,pan,tone,rate):
 result=bytearray(32000)
 lines=[(8,'AMIXER / VOLUME + PAN'),(32,'SPACE: PLAY  2: LOOPING SECOND VOICE'),(48,'UP/DOWN: VOLUME  LEFT/RIGHT: PAN'),(64,'F1: LEFT  F2: CENTRE  F3: RIGHT'),(80,'ESC: EXIT'),(104,'VOLUME %3d / 255   PAN %3d / 255'%(volume,pan)),(120,'SECOND VOICE: '+('ON'if tone else'OFF')),(144,('25'if rate==2 else'12.5')+' KHZ STEREO / TWO PCM VOICES'),(160,'F4: SWITCH 12.5 / 25 KHZ')]
 for y,line in lines:
  for i,c in enumerate(line):
   for row in range(8):result[(y+row)*160+(i//2)*8+i%2]=font[(ord(c)-32)*8+row]
 return bytes(result)
with HatariSession(str(release),tos=str(Path.home()/'Atari/tos/TOS v1.62 (1990)(Atari Corp)(STE)(De).img'),machine='ste',sound=True,debug_except='bus,address,illegal',extra_args=['--confirm-quit','false','--memsize','1','--cpuclock','8','--monitor','rgb'])as h:
 h.wait(9);base=h.basepage()['text'];a=lambda n:base+sy[n]
 def dump(addr,size):
  p=out/'dump.bin';p.unlink(missing_ok=True);h.debug('savebin %s $%x $%x'%(p,addr,size),settle=.05)
  for _ in range(300):
   if p.exists()and p.stat().st_size==size:return p.read_bytes()
   time.sleep(.01)
  raise AssertionError(('dump timeout',h.lines[-10:]))
 def tap(scan):
  h.control('hatari-event keydown '+str(scan).zfill(2),settle=.12)
  h.control('hatari-event keyup '+str(scan).zfill(2),settle=.12)
 def check(volume,pan,tone,rate=2):
  h.wait(.5);want=expected(volume,pan,tone,rate)
  # Freeze on the VBL callback; main-thread rendering is already quiescent.
  h.debug('b pc = $%x :once'%a('AudioMixer_Vbl'),settle=.1)
  for name in ('gScreenLogicGraphic','gScreenPhysicGraphic'):
   p=out/'dump.bin';p.unlink(missing_ok=True);h.stdin_cmd('savebin %s $%x 4'%(p,a(name)),settle=.02)
   ptr=struct.unpack('>I',p.read_bytes())[0]
   p.unlink();h.stdin_cmd('savebin %s $%x $7d00'%(p,ptr),settle=.02)
   raw=p.read_bytes();assert raw==want,(name,next((i,u,v)for i,(u,v)in enumerate(zip(raw,want))if u!=v))
  if tone:
   im=Image.new('RGB',(320,200));im.putdata([(255,255,255)if raw[y*160+(x//16)*8+(x%16)//8]&(1<<(7-x%8))else(0,0,0)for y in range(200)for x in range(320)])
   im.resize((640,400),Image.Resampling.NEAREST).save(out/'preview.png')
  h.stdin_cmd('c',settle=.05)
 check(192,128,False)
 tap(60);tap(61);tap(75);tap(72);tap(3);tap(57)
 h.wait(1);check(208,239,True)
 # Read the actual public voice state, confirming the second loop is active.
 v=dump(a('gAudioMixerSamples'),56);assert (v[18],v[20],v[47])==(208,239,1)
 tap(62);check(208,239,True,1);assert dump(0xffff8921,1)[0]&3==1
 tap(62);check(208,239,True,2);assert dump(0xffff8921,1)[0]&3==2
 tap('01');h.wait(.5)
 assert not any('Bus Error'in l or 'Address Error'in l or 'CPU exception'in l for l in h.lines),h.lines[-20:]
 assert h.basepage()['text']!=base,h.lines[-20:]
 report={'result':'PASS','release_sha256':hashlib.sha256(binary).hexdigest(),'full_display_page_checks':8,'keys':'F2 F3 LEFT UP 2 SPACE F4 F4 ESC','live_output_rates':[12517,25033],'voice0_volume':208,'voice0_pan':239,'voice1_loop_active':True,'return_to_TOS':True}
 (out/'ui-verification.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
 (out/'dump.bin').unlink(missing_ok=True)
