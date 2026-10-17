"""Compare complete star area against independent projection / planar renderer."""
from pathlib import Path
import json,os,struct,subprocess,sys,time
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
sys.path.insert(0,str(Path.home()/'.codex/skills/hatari-debugging/scripts'))
from hatari_session import HatariSession
root=Path(__file__).resolve().parents[1]
sym={p[2]:int(p[0],16) for l in subprocess.check_output(['m68k-atari-mintelf-nm',str(root/'analysis/SDBG.PRG')],text=True).splitlines() if len(p:=l.split())==3}
roms=[('st','2.06','TOS v2.06 (1991)(Atari Corp)(Mega-STE)(UK).img'),('ste','2.06','TOS v2.06 (1991)(Atari Corp)(Mega-STE)(UK).img'),('ste','1.62','TOS v1.62 (1990)(Atari Corp)(STE)(GB)[STE TOS, Rev 2].img')]
if len(sys.argv)>1:roms=[c for c in roms if c[0]+'-'+c[1]==sys.argv[1]]
results=[]
for machine,version,rom in roms:
 label=machine+'-'+version
 with HatariSession(str(root/'STARS.PRG'),machine=machine,sound=False,screenshot_dir=str(root/'analysis/shots'/label/str(int(time.time()))),debug_except='bus,address,illegal',extra_args=['--tos',str(Path.home()/'Atari/tos'/rom),'--confirm-quit','false','--memsize','1','--cpuclock','8','--cpulevel','0','--monitor','rgb']) as h:
  h.wait(16);shot=h.screenshot();base=h.basepage()['text']
  def addr(n):return base+sym[n]
  def block(a,n):
   path=root/'analysis/target.bin';h.stdin_cmd('savebin %s $%x $%x'%(path,a,n));b=path.read_bytes();path.unlink();assert len(b)==n;return b
  def word(n):
   a=addr(n);return h.mem(a,2).u16(a)
  def stop(n):h.debug('b pc = $%x :once'%addr(n));h.wait(.2)
  stop('Stars_Draw')
  state=block(addr('gStarsCodeBytes'),40)
  print(label,'state',state.hex(),flush=True)
  assert struct.unpack_from('>H',state,sym['gStarsReady']-sym['gStarsCodeBytes'])[0]==1
  h.stdin_cmd('c')
  pages=set();checks=[]
  for key,count in [('4',768),('1',96),('3',384),('2',192)]:
   h.tap(key);h.wait(2)
   for repeat in range(2):
    if not repeat:stop('Stars_Draw')
    ptr=struct.unpack('>I',block(addr('gStarsScreen'),4))[0];pages.add(ptr)
    z=struct.unpack('>'+str(count*2)+'I',block(addr('gStarsZ'),count*8))
    old=block(ptr,152*160);assert old==bytes(len(old)),(label,count,'erase left pixels')
    expected=bytearray(len(old));visible=0
    for i in range(count):
     tx,dx=divmod((z[i*2]-addr('gStarsPreX'))//2,128)
     ty,dy=divmod((z[i*2+1]-addr('gStarsPreY'))//2,128)
     assert dx==dy and 0<=tx<320 and 0<=ty<152,(i,tx,ty,dx,dy)
     x=int((tx-160)*32/(127-dx+21))+160
     y=int((ty-76)*32/(127-dx+32))+76
     if not 0<=x<320 or dx==127:continue
     visible+=1;c=min(6,dx//21+1);o=y*160+(x//16)*8+bool(x&8);bit=128>>(x&7)
     for plane in range(3):
      if c&(1<<plane):expected[o+plane*2]|=bit
    h.stdin_cmd('b pc = $%x :once'%addr('Screen_Update'));h.stdin_cmd('c');h.wait(.2)
    actual=block(ptr,len(expected))
    assert actual==expected,(label,count,next((i,a,b) for i,(a,b) in enumerate(zip(actual,expected)) if a!=b))
    if not repeat:h.stdin_cmd('b pc = $%x :once'%addr('Stars_Draw'))
    h.stdin_cmd('c');h.wait(.1);checks.append({'count':count,'visible_stars':visible,'page':ptr})
   print(label,'PASS count',count,'both pages',flush=True)
  assert len(pages)==2
  h.tap('SPACE');stop('Vbl_WaitVbl');assert struct.unpack('>H',block(addr('gStarsPaused'),2))[0]==1
  frozen=block(addr('gStarsZ'),768*8);frames=block(addr('gStarsFrames'),4)
  h.stdin_cmd('c');h.wait(1);stop('Vbl_WaitVbl')
  assert block(addr('gStarsZ'),768*8)==frozen and block(addr('gStarsFrames'),4)==frames
  h.stdin_cmd('c');h.tap('SPACE');h.wait(.5);stop('Stars_Draw')
  assert struct.unpack('>H',block(addr('gStarsPaused'),2))[0]==0
  h.stdin_cmd('c')
  h.control('hatari-event keydown 01');h.wait(.3);h.control('hatari-event keyup 01');h.wait(5)
  assert word('gStarsExited')==1
  assert not any(any(e in l for e in ('Bus Error','Address Error','Illegal instruction')) for l in h.lines)
  results.append({'machine':machine,'tos':version,'ram_mb':1,'projection_and_all_24320_frame_bytes_match':True,'both_pages_verified':True,'checks':checks,'pause_resume_exit':True,'screenshot':shot})
(root/('analysis/results'+('-'+sys.argv[1] if len(sys.argv)>1 else '')+'.json')).write_text(json.dumps(results,indent=2)+'\n')
