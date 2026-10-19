"""Native runtime regressions: layout, page dirty masks, script safety and PCM."""
from pathlib import Path
import os,sys,time,struct,json,hashlib
os.environ.setdefault('SDL_VIDEODRIVER','dummy');os.environ.setdefault('SDL_AUDIODRIVER','dummy')
sys.path.insert(0,str(Path.home()/'.agents/skills/hatari-debugging/scripts'))
from hatari_session import HatariSession,nm_symbols
r=Path(__file__).resolve().parents[1];out=r/'analysis';prg=out/'CUTTEST.PRG'
sy=nm_symbols(str(prg),nm='m68k-atari-mintelf-nm')
font=(r/'assets/FONT.BIN').read_bytes()
def glyph(x,y,c,frame):
 for yy in range(6):
  for xx in range(6):
   # The font sheet has 20 columns of 16-pixel cells; only 6 are used.
   sx=(ord(c)%20)*16+xx;sy=(ord(c)//20)*6+yy
   colour=sum(((struct.unpack_from('>H',font,sy*160+(sx//16)*8+p*2)[0]>>(15-sx%16))&1)<<p for p in range(4))
   if colour:
    for p in range(4):
     at=(y+yy)*160+((x+xx)//16)*8+p*2
     word=struct.unpack_from('>H',frame,at)[0];bit=1<<(15-(x+xx)%16)
     struct.pack_into('>H',frame,at,(word|bit)if(colour>>p)&1 else(word&~bit))
def label(frame,text,x,y):
 for c in text:glyph(x,y,c,frame);x+=6
with HatariSession(str(prg),tos=str(Path.home()/'Atari/tos/TOS v1.62 (1990)(Atari Corp)(STE)(De).img'),machine='ste',sound=True,debug_except='bus,address,illegal',extra_args=['--confirm-quit','false','--memsize','1','--cpuclock','8','--monitor','rgb'])as h:
 h.wait(10);base=h.basepage()['text'];a=lambda n:base+sy[n]
 h.debug('b pc = $%x :once'%a('CutTest_Marker'),settle=.3)
 def dump(addr,size):
  p=out/'runtime-dump.bin';p.unlink(missing_ok=True);h.stdin_cmd('savebin %s $%x $%x'%(p,addr,size),settle=.02)
  for _ in range(300):
   if p.exists()and p.stat().st_size==size:return p.read_bytes()
   time.sleep(.01)
  raise AssertionError(('dump timeout',h.lines[-20:]))
 def word(n):return struct.unpack('>H',dump(a(n),2))[0]
 castle=dump(a('Cut_Castle')+34,32000)
 for stage in range(1,6):
  assert word('gTestStage')==stage,(word('gTestStage'),h.lines[-10:])
  assert word('gTestError')==0,word('gTestError')
  if stage<5:
   expected=bytearray(castle if stage in (1,2)else bytes(32000))
   if stage==1:
    for text,x,y in [('AB',100,30),('CD',100,38),('E',136,38),('FG',100,46)]:label(expected,text,x,y)
   elif stage==2:
    label(expected,'HI JK LM',100,30);label(expected,'NO PQ',100,38)
   elif stage==4:
    label(expected,'A'*10,100,30);label(expected,'A'*10,100,38);label(expected,'A'*5,100,46)
   for name in ('gScreenLogicGraphic','gScreenPhysicGraphic'):
    ptr=struct.unpack('>I',dump(a(name),4))[0];actual=dump(ptr,32000)
    assert actual==expected,(stage,name,next((i,u,v)for i,(u,v)in enumerate(zip(actual,expected))if u!=v))
  else:assert word('gTestDone')==1
  h.stdin_cmd('b pc = $%x :once'%a('CutTest_Marker'),settle=.01)if stage<5 else None
  h.stdin_cmd('w $%x 0 1'%a('gTestAdvance'),settle=.01);h.stdin_cmd('c',settle=.8)
 assert not any(any(x in l for x in ('Bus Error','Address Error','Illegal instruction'))for l in h.lines),h.lines[-20:]
 report={'result':'PASS','program_sha256':hashlib.sha256(prg.read_bytes()).hexdigest(),'full_frame_checks':8,'tests':['background set/clear on both pages without callbacks or external copies','repeated Render on one page retains dirty state for other page','CRLF LF TAB consumption and bounded text rectangle','word wrapping uses X + WIDTH','TEXT_PAGE_SET redraws and removes previous caption while enabled','259-character token without stack overflow or out-of-rectangle writes','Stop/empty/missing/recursive scripts terminate safely','VAR parser member table terminator','two simultaneous samples, volume/pan, third-voice stealing, SAMPLE_DISABLE','looped sample remains active, SAMPLE_WAIT blocks for one-shot and DMA tail','Stop clears both voices and all queued PCM','natural script return and clean teardown']}
 (out/'runtime-verification.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
 (out/'runtime-dump.bin').unlink(missing_ok=True)
