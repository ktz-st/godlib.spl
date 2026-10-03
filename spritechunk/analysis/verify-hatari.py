"""Check per-page chunk restoration on ST CPU and STE blitter paths."""
import subprocess,sys,struct
from pathlib import Path
sys.path.insert(0,str(Path.home()/'.codex/skills/hatari-debugging/scripts'))
from hatari_session import HatariSession
root=Path(__file__).resolve().parents[1]
lines=subprocess.check_output(['m68k-atari-mintelf-nm','-n',str(root/'analysis/SPRCHDBG.PRG')],text=True)
syms={p[2]:int(p[0],16) for line in lines.splitlines() if len(p:=line.split())==3}
for machine in ('st','ste'):
 with HatariSession(str(root/'SPRCHUNK.PRG'),machine=machine,
  screenshot_dir=str(root/'analysis/shots'/machine),sound=False,
  debug_except='bus,address,illegal',extra_args=['--memsize','4','--monitor','rgb']) as h:
  h.wait(8); base=h.basepage()['text']
  def addr(name): return base+syms[name]
  def pos():
   m=h.mem(addr('gSpriteChunkPos'),4);return m.s16(addr('gSpriteChunkPos')),m.s16(addr('gSpriteChunkPos')+2)
  def counts():
   a=addr('gRestoredChunks');m=h.mem(a,4);return m.u16(a),m.u16(a+2)
  assert h.mem(addr('gSpriteChunkReady'),2).u16(addr('gSpriteChunkReady'))==1
  h.tap('3'); start=pos(); before=counts()
  h.tap('RIGHT',hold=1.0); assert pos()[0]>start[0]
  after=counts();assert after[0]>before[0] and after[1]>before[1]
  h.wait(.3);assert counts()==after  # no redraw/restore when stationary
  print(machine,'movement',start,'->',pos(),'restored chunks',after,flush=True)
  # Exercise both clamps and all bit phases while traversing the screen.
  h.tap('LEFT',hold=6.5); h.tap('UP',hold=4.5); assert pos()==(0,0)
  h.tap('RIGHT',hold=6.5); h.tap('DOWN',hold=4.5); assert pos()==(304,184)
  h.tap('LEFT',hold=.5); h.tap('UP',hold=.5); h.wait(.3)
  x,y=pos()
  a=addr('sChunkLists');m=h.mem(a,264)
  for page in (0,1):
   p=a+page*132
   assert m.u16(p)==((x+15)//16-x//16+1)
   assert m.u16(p+4)==y*160+(x//16)*8
   assert m.u16(p+6)==16
  # Read both displayed/drawing pages after input has stopped. Every pixel
  # outside the current sprite must equal the clean background (including HUD).
  def vram(canvas):
   a=addr(canvas);return h.mem(a,4).u32(a)
  back=vram('gScreenBackGraphic'); reference=h.mem(back,32000).bytes(back,32000)
  for canvas in ('gScreenLogicGraphic','gScreenPhysicGraphic'):
   a=vram(canvas);actual=h.mem(a,32000).bytes(a,32000)
   assert actual!=reference,'sprite not drawn'
   for yy in range(200):
    for xx in range(0,320,16):
     allowed=0
     if y<=yy<y+16:
      allowed=sum(1<<(15-i) for i in range(16) if x<=xx+i<x+16)
     offset=yy*160+(xx//16)*8
     for plane in range(4):
      offset_plane=offset+plane*2
      old=struct.unpack_from('>H',reference,offset_plane)[0]
      new=struct.unpack_from('>H',actual,offset_plane)[0]
      assert ((old^new)&(~allowed&65535))==0,(machine,canvas,xx,yy)
  print(machine,'verified both pages: no trails; shot',h.screenshot(),flush=True)
  h.tap('SPACE');h.wait(1)
  print(machine,'exit',h.screenshot(),flush=True)
  assert not any('Address Error' in l or 'Bus Error' in l or 'Exception' in l for l in h.lines)
print('PASS: ST/STE, separate lists, movement, four edges, unchanged-frame skip, no trails and exit')
