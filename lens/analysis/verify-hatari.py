"""Compare real planar RAM against an independent per-pixel reference for planar compositing."""
from pathlib import Path
import json,os,struct,subprocess,sys,time,math
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
sys.path.insert(0,str(Path.home()/'.agents/skills/hatari-debugging/scripts'))
from hatari_session import HatariSession
root=Path(__file__).resolve().parents[1]
sym={p[2]:int(p[0],16) for l in subprocess.check_output(['m68k-atari-mintelf-nm',str(root/'analysis/LNSDB.PRG')],text=True).splitlines() if len(p:=l.split())==3}
configs=[('st','2.06','TOS v2.06 (1991)(Atari Corp)(Mega-STE)(UK).img'),('ste','2.06','TOS v2.06 (1991)(Atari Corp)(Mega-STE)(UK).img'),('ste','1.62','TOS v1.62 (1990)(Atari Corp)(STE)(GB)[STE TOS, Rev 2].img')]
if len(sys.argv)>1:configs=[c for c in configs if c[0]+'-'+c[1]==sys.argv[1]]
results=[]
for machine,version,rom in configs:
 tag=machine+'-'+version
 with HatariSession(str(root/'LENS.PRG'),machine=machine,sound=False,screenshot_dir=str(root/'analysis/shots'/tag/str(int(time.time()))),debug_except='bus,address,illegal',extra_args=['--tos',str(Path.home()/'Atari/tos'/rom),'--confirm-quit','false','--memsize','1','--cpuclock','8','--cpulevel','0','--monitor','rgb','--trace','ikbd_cmds']) as h:
  h.wait(12);base=h.basepage()['text'];shot=h.screenshot()
  def addr(n):return base+sym[n]
  def stop():h.debug('b pc = $%x :once'%addr('Screen_Update'))
  def dump(a,size,name):
   p=root/('analysis/temp-'+tag+'-'+name+'.bin');p.unlink(missing_ok=True)
   h.stdin_cmd('savebin %s $%x $%x'%(p,a,size),settle=.03)
   for i in range(200):
    if p.exists() and p.stat().st_size==size:break
    time.sleep(.01)
   data=p.read_bytes();assert len(data)==size;p.unlink();return data
  first=min(v for k,v in sym.items() if k.startswith('gFx'));last=max(v+4 for k,v in sym.items() if k.startswith('gFx'))
  def state():return dump(base+first,last-first,'state')
  def word(s,n):return struct.unpack_from('>H',s,sym[n]-first)[0]
  def lng(s,n):return struct.unpack_from('>I',s,sym[n]-first)[0]
  def step():h.stdin_cmd('b pc = $%x :once'%addr('Screen_Update'),settle=.02);h.stdin_cmd('c',settle=.04)
  stop();s=state();assert word(s,'gFxReady')==1
  bgptr=struct.unpack('>I',dump(addr('gScreenClass')+12,4,'backptr'))[0];background=dump(bgptr,32000,'background')
  pages=set();checks=0
  centers=set()
  mouseaddr=struct.unpack('>I',dump(addr('IKBD_GetMouseX')+2,4,'mouse-x'))[0]
  assert struct.unpack('>I',dump(addr('IKBD_GetMouseY')+2,4,'mouse-y'))[0]==mouseaddr+2
  def signed(s,n):return struct.unpack_from('>h',s,sym[n]-first)[0]
  def check():
   global checks
   s=state();page=lng(s,'gFxScreen');want=bytearray(background);cx=signed(s,'gFxX');cy=signed(s,'gFxY')
   for dy in range(-32,32):
    for dx in range(-32,32):
     r2=dx*dx+dy*dy
     if r2>=1024:continue
     if r2>=31.3**2:colour=15
     else:
      f=1/(1+(1-r2/1024)**1.25);sx=cx+round(dx*f);sy=cy+round(dy*f)
      off=sy*160+(sx//16)*8;bit=15-(sx&15)
      colour=sum(((int.from_bytes(background[off+p*2:off+p*2+2],'big')>>bit)&1)<<p for p in range(4))
     x=cx+dx;y=cy+dy;off=y*160+(x//16)*8;mask=1<<(15-(x&15))
     for p in range(4):
      w=int.from_bytes(want[off+p*2:off+p*2+2],'big');w=(w&~mask)|(mask if colour&(1<<p) else 0)
      want[off+p*2:off+p*2+2]=w.to_bytes(2,'big')
   actual=dump(page,32000,'screen')
   assert actual==want,(tag,cx,cy,hex(bgptr),hex(page),next(((i,a,b) for i,(a,b) in enumerate(zip(actual,want)) if a!=b),None))
   centers.add((cx,cy));pages.add(page);checks+=1;return s
  check();step();check()
  # Inject the input-side IKBD coordinates, not the renderer coordinates.
  # Derive the actual input addresses from the relocated mouse getter code.
  points=[(x,100) for x in range(144,160)]+[(0,0),(319,0),(0,199),(319,199),(0,100),(319,100),(160,0),(160,199),(-20,-20),(340,220),(160,100)]
  for x,y in points:
   packet=struct.pack('>hh',x,y)
   h.stdin_cmd('w $%x %s'%(mouseaddr,' '.join(str(v) for v in packet)),settle=.02)
   step();s=check();assert (signed(s,'gFxX'),signed(s,'gFxY'))==(min(287,max(32,x)),min(167,max(32,y))), (x,y,signed(s,'gFxX'),signed(s,'gFxY'))
   step();check()
  assert len(pages)==2
  h.stdin_cmd('c',settle=.03);h.tap('A');stop();s=check();assert word(s,'gFxAuto')==1
  for i in range(40):step();check()
  h.stdin_cmd('c',settle=.03);h.tap('M');h.tap('R');stop();s=check()
  assert word(s,'gFxAuto')==0 and word(s,'gFxRaster')==1
  assert any('IKBD_Cmd_RelMouseMode' in l for l in h.lines)
  missed=lng(s,'gFxMissedVbl');assert missed==0,(tag,missed)
  h.stdin_cmd('c',settle=.03);h.control('hatari-event keydown 01');h.wait(.2);h.control('hatari-event keyup 01');h.wait(4)
  assert h.mem(addr('gFxExited'),2).u16(addr('gFxExited'))==1
  (root/('analysis/verification-'+tag+'.log')).write_text('\n'.join(h.lines))
  faults=[l for l in h.lines if any(e in l for e in ['Bus Error','Address Error','Illegal instruction'])]
  assert not faults,faults
  result={'machine':machine,'tos':version,'cpu_mhz':8,'ram_mb':1,'full_screen_checks':checks,'both_pages':True,'controls_and_exit':True,'missed_vbl':missed,'screenshot':shot}
  (root/('analysis/results-'+tag+'.json')).write_text(json.dumps(result,indent=2)+'\n');results.append(result);print(tag,'PASS',result,flush=True)
(root/'analysis/results.json').write_text(json.dumps(results,indent=2)+'\n')
