"""Native text-parser/player integration: complete frames, timeline and controls."""
from pathlib import Path
import os,sys,time,struct,json,hashlib
from PIL import Image
os.environ.setdefault('SDL_VIDEODRIVER','dummy');os.environ.setdefault('SDL_AUDIODRIVER','dummy')
sys.path.insert(0,str(Path.home()/'.agents/skills/hatari-debugging/scripts'))
from hatari_session import HatariSession,nm_symbols
r=Path(__file__).resolve().parents[1];out=r/'analysis';sy=nm_symbols(str(out/'CUTDBG.PRG'),nm='m68k-atari-mintelf-nm')
def unpack(raw,w,h):
 result=[]
 for y in range(h):
  for x in range(0,w,16):
   words=struct.unpack_from('>4H',raw,y*w//2+x//2)
   result.extend(sum(((v>>(15-b))&1)<<p for p,v in enumerate(words))for b in range(16))
 return result
def packed(idx):
 result=bytearray()
 for y in range(200):
  for x in range(0,320,16):
   for p in range(4):result+=struct.pack('>H',sum(((idx[y*320+x+b]>>p)&1)<<(15-b)for b in range(16)))
 return bytes(result)
def preview(raw,pal,path):
 words=struct.unpack('>16H',pal);rgb=[tuple(((((v>>s)&7)<<1)|(((v>>s)>>3)&1))*17 for s in (8,4,0))for v in words]
 im=Image.new('RGB',(320,200));im.putdata([rgb[c]for c in unpack(raw,320,200)]);im.resize((640,400),Image.Resampling.NEAREST).save(path)
font=unpack((r/'assets/FONT.BIN').read_bytes(),320,200)
starbytes=(r/'assets/STAR.BIN').read_bytes();stars=[unpack(starbytes[i*160+32:(i+1)*160],16,16)for i in range(3)]
results=[]
for machine in ('ste','st'):
 tos='TOS v1.62 (1990)(Atari Corp)(STE)(De).img'if machine=='ste'else'TOS v2.06 (1991)(Atari Corp)(Mega-STE)(UK).img'
 with HatariSession(str(r/'CUTSCENE.PRG'),tos=str(Path.home()/'Atari/tos'/tos),machine=machine,sound=True,debug_except='bus,address,illegal',extra_args=['--confirm-quit','false','--memsize','1','--cpuclock','8','--monitor','rgb'])as h:
  h.wait(10);base=h.basepage()['text'];a=lambda n:base+sy[n]
  h.debug('b pc = $%x :once'%a('CutExample_FrameDone'),settle=.4)
  def step():
   h.stdin_cmd('b pc = $%x :once'%a('CutExample_FrameDone'),settle=.002);mark=len(h.lines);h.stdin_cmd('c',settle=.005)
   for _ in range(300):
    if any('breakpoint'in l.lower()and'match'in l.lower()for l in h.lines[mark:]):break
    time.sleep(.01)
   else:raise AssertionError(('no frame breakpoint',h.lines[-15:]))
  def dump(addr,size):
   path=out/'dump.bin';path.unlink(missing_ok=True);h.stdin_cmd('savebin %s $%x $%x'%(path,addr,size),settle=.003)
   for _ in range(300):
    if path.exists()and path.stat().st_size==size:break
    time.sleep(.005)
   data=path.read_bytes();assert len(data)==size;return data
  def word(n):return struct.unpack('>H',dump(a(n),2))[0]
  def ptr(n):return struct.unpack('>I',dump(a(n),4))[0]
  def key(scan):
   h.control('hatari-event keydown '+scan,settle=.03);step();h.control('hatari-event keyup '+scan,settle=.02);step()
  assert word('gCutReady')==1
  scene=ptr('gCutScene');header=dump(scene,56);counts=struct.unpack_from('>8H',header,40)
  assert counts==(2,8,4,3,1,4,1,0),counts
  spr=struct.unpack_from('>I',header,28)[0];txt=struct.unpack_from('>I',header,32)[0]
  source=[dump(a(name)+34,32000)for name in ('Cut_Castle','Cut_Forest')]
  idx=[unpack(data,320,200)for data in source]
  replays=struct.unpack('>I',dump(a('gCutReplays'),4))[0];key('19')
  assert struct.unpack('>I',dump(a('gCutReplays'),4))[0]==replays+1
  pages=set();frames=set();captions=set();positions={1:set(),2:set()};checks=0;seen_callbacks=set();last_done=False;audio_seen=set()
  for tick in range(1800):
   step()
   if tick%8 not in (0,1):continue
   audio=struct.unpack('>4H',dump(a('gCutAudio'),8));audio_seen.update(i for i,v in enumerate(audio)if v)
   done=word('gCutDone');callback=word('gCutCallbacks');seen_callbacks.add(callback)
   if done:last_done=True;break
   if not callback:continue
   assert callback in (1,2),callback
   sprite=dump(spr,76);text=dump(txt,66)
   x,y=struct.unpack_from('>2h',sprite,32);frame=word('gCutSpriteFrame');enabled=struct.unpack_from('>H',sprite,74)[0]
   bg=struct.unpack('>I',dump(a('gCutSceneSysClass')+8,4))[0]
   bgdata=struct.unpack('>I',dump(bg+12,4))[0]
   display_scene=1 if bgdata==a('Cut_Castle')else 2
   expected=idx[display_scene-1].copy()
   if enabled:
    frames.add(frame);positions[display_scene].add((x,y));assert 0<=frame<3
    for yy in range(16):
     for xx in range(16):
      col=stars[frame][yy*16+xx]
      if col:expected[(y+yy)*320+x+xx]=col
   if struct.unpack_from('>H',text,52)[0]:
    page=struct.unpack_from('>I',text,32)[0];string=struct.unpack_from('>I',dump(page,8),4)[0]
    label=dump(string,100).split(b'\0')[0].decode('ascii');label=' '.join(label.split());captions.add(label)
    px,py=struct.unpack_from('>2h',text,24)
    for letter in label:
     c=ord(letter)
     for yy in range(6):
      for xx in range(6):
       if font[(c//20*6+yy)*320+c%20*16+xx]:expected[(py+yy)*320+px+xx]=15
     px+=6
   screen=ptr('gScreenLogicGraphic');actual=dump(screen,32000);wanted=packed(expected)
   assert actual==wanted,(machine,tick,callback,(x,y,frame,enabled),next((i,u,v)for i,(u,v)in enumerate(zip(actual,wanted))if u!=v))
   pages.add(screen);checks+=1
   if machine=='ste'and enabled and ((display_scene==1 and 120<x<160)or(display_scene==2 and 130<x<180)):
    preview(actual,dump(0xffff8240,32),out/('castle.png'if display_scene==1 else'forest.png'))
  assert audio_seen==({0,1,2,3}if machine=='ste'else set()),audio_seen
  assert last_done and seen_callbacks>={1,2},(last_done,seen_callbacks)
  assert len(pages)==2 and frames=={0,1,2}and len(captions)==4,(pages,frames,captions)
  assert len(positions[1])>8 and len(positions[2])>5,positions
  for _ in range(4):step()
  logic=dump(ptr('gScreenLogicGraphic'),32000);physic=dump(ptr('gScreenPhysicGraphic'),32000)
  assert logic==physic and any(logic)
  # Actual keyboard routes: replay, restart while playing, skip, replay, exit.
  key('57');assert word('gCutDone')==0
  key('19');assert word('gCutDone')==0
  key('57');assert word('gCutDone')==1
  key('57');assert word('gCutDone')==0
  h.stdin_cmd('c',settle=.1);h.control('hatari-event keydown 01',settle=.15);h.control('hatari-event keyup 01',settle=.5)
  assert h.mem(a('gCutExited'),2).u16(a('gCutExited'))==1
  assert not any(any(msg in l for msg in ('Bus Error','Address Error','Illegal instruction'))for l in h.lines)
  result={'machine':machine,'TOS':tos,'full_frame_checks':checks,'captions':sorted(captions),'animation_frames':sorted(frames),'display_pages':len(pages),'script_background_callbacks':2,'narration_samples_seen':sorted(audio_seen),'natural_finish':True,'replay_restart_skip_exit':True}
  results.append(result);print('PASS',result,flush=True)
(out/'dump.bin').unlink(missing_ok=True)
(out/'verification.json').write_text(json.dumps({'program_sha256':hashlib.sha256((r/'CUTSCENE.PRG').read_bytes()).hexdigest(),'configuration':'68000, 8 MHz, 1 MiB, PAL RGB','method':'Native CutScene_Parse text and actual script runtime. Full 32000-byte logical frame comparisons against independent source image + selected twinkle frame + 6x6 caption compositor, adjacent display-page pairs every eighth script update; both scenes/pages, all captions/animation frames. Natural return plus real keyboard restart/replay/skip/exit.','results':results},indent=2)+'\n')
