"""Verify packed glyph scrolling, planar output and no missed PAL VBLs."""
from pathlib import Path
import json,os,re,struct,subprocess,sys,time
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
sys.path.insert(0,str(Path.home()/'.codex/skills/hatari-debugging/scripts'))
from hatari_session import HatariSession
root=Path(__file__).resolve().parents[1]
sym={p[2]:int(p[0],16) for l in subprocess.check_output(['m68k-atari-mintelf-nm',str(root/'analysis/FDBG.PRG')],text=True).splitlines() if len(p:=l.split())==3}
source=(root/'fastscroll.c').read_text().split('static const char gText[]=')[1].split(';',1)[0]
message=''.join(json.loads(t) for t in re.findall(r'"[^"]*"',source));font=(root/'assets/BUGSY.BIN').read_bytes()
tos206=os.environ.get('HATARI_TOS','/Users/kriss/Atari/tos/TOS v2.06 (1991)(Atari Corp)(Mega-STE)(UK).img')
tos162=os.environ.get('HATARI_TOS162','/Users/kriss/Atari/tos/TOS v1.62 (1990)(Atari Corp)(STE)(GB)[STE TOS, Rev 2].img')
configs=[('st','2.06',tos206),('ste','2.06',tos206),('ste','1.62',tos162)]
if len(sys.argv)>1:configs=[c for c in configs if c[0]+'-'+c[1]==sys.argv[1]]
results=[]
for machine,version,tos in configs:
 label=machine+'-'+version;shots=root/'analysis/shots'/label/str(int(time.time()))
 with HatariSession(str(root/'FSCRL.PRG'),machine=machine,sound=False,screenshot_dir=str(shots),debug_except='bus,address,illegal',extra_args=['--tos',tos,'--confirm-quit','false','--memsize','1','--cpulevel','0','--cpuclock','8','--monitor','rgb']) as h:
  h.wait(8);base=h.basepage()['text']
  def addr(n):return base+sym[n]
  def raw(n,size,paused=False):return h.mem(addr(n),size,paused=paused).bytes(addr(n),size)
  def word(n):return struct.unpack('>H',raw(n,2))[0]
  def long(n):return struct.unpack('>I',raw(n,4))[0]
  assert word('gScrollReady')==1
  h.tap('SPACE');assert word('gScrollPaused')==1
  def check():
   h.debug('b pc = $%x :once'%addr('Screen_Update'));h.wait(.1)
   buf=raw('gScrollBuffer',1188,True)
   current=(struct.unpack('>H',raw('gScrollTextPos',2,True))[0]-1)%len(message)
   phase=struct.unpack('>H',raw('gScrollGlyphPixel',2,True))[0]
   expected=bytearray(1188)
   for x in range(352):
    relative=x-(320-phase);offset=relative//32;gx=relative%32
    ch=message[(current+offset)%len(message)] if offset<=0 else ' '
    for y in range(27):
     if font[(ord(ch)-32)*108+y*4+gx//8]&(128>>(gx&7)):expected[y*44+x//8]|=128>>(x&7)
   assert buf==expected,(label,'glyph conveyor',current,phase)
   page=struct.unpack('>I',raw('gScrollScreen',4,True))[0];dump=root/('analysis/screen-'+label+'.bin')
   h.stdin_cmd('savebin %s $%x $7d00'%(dump,page));screen=dump.read_bytes();dump.unlink()
   for y in range(27):
    for group in range(20):
     start=(86+y)*160+group*8
     assert screen[start:start+8]==buf[y*44+group*2:y*44+group*2+2]+b'\0'*6,(label,y,group)
   h.stdin_cmd('c');h.screenshot();print(label,'PASS glyphs and planar strip',current,phase,flush=True)
  check()
  for key,speed in [('1',1),('2',2),('3',4),('4',8)]:
   h.tap(key);assert word('gScrollSpeed')==speed
   h.tap('SPACE');assert word('gScrollPaused')==0;h.wait(1)
   h.tap('SPACE');assert word('gScrollPaused')==1;check()
  # Let the fastest setting cross the message wrap and keep drawing every VBL.
  h.tap('SPACE');h.wait(18);h.tap('SPACE');assert word('gScrollPaused')==1;check()
  frames=long('gScrollFrames');missed=long('gScrollMissedVbl');assert missed==0,(label,frames,missed)
  h.control('hatari-event keydown 01');h.wait(.3);h.control('hatari-event keyup 01');h.wait(5)
  assert word('gScrollExited')==1
  assert not any(any(e in l for e in ('Bus Error','Address Error','Illegal instruction')) for l in h.lines)
  results.append({'machine':machine,'tos':version,'ram_mb':1,'frames':frames,'missed_vbl':missed,'all_four_speeds_and_message_wrap':True,'glyph_and_planar_comparison':True,'exit':True})
(root/('analysis/results'+('-'+sys.argv[1] if len(sys.argv)>1 else '')+'.json')).write_text(json.dumps(results,indent=2)+'\n')
