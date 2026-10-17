"""Compare complete rendered pages against the imported STF artwork during replay."""
from pathlib import Path
import os,sys,struct,json,time
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
sys.path.insert(0,str(Path.home()/'.agents/skills/hatari-debugging/scripts'))
from hatari_session import HatariSession,nm_symbols
root=Path(__file__).resolve().parents[1]
sym=nm_symbols(str(root/'analysis/WIZDBG.PRG'),nm='m68k-atari-mintelf-nm')
frames=bytes(1200)+(root.parent/'lancemod/assets/STF_VU.DAT').read_bytes()
results=[]
for version,rom in [('2.06','TOS v2.06 (1991)(Atari Corp)(Mega-STE)(UK).img'),('1.62','TOS v1.62 (1990)(Atari Corp)(STE)(GB)[STE TOS, Rev 2].img'),('1.62-de','TOS v1.62 (1990)(Atari Corp)(STE)(De).img')]:
 if version!=(sys.argv[1] if len(sys.argv)>1 else '1.62-de'):continue
 with HatariSession(str(root/'WIZZCAT.TOS'),screenshot_dir=str(root/'analysis/shots'/version),debug_except='bus,address,illegal',extra_args=['--tos',str(Path.home()/'Atari/tos'/rom),'--memsize','1','--cpuclock','8','--cpulevel','0','--monitor','rgb','--confirm-quit','false']) as h:
  h.wait(8);base=h.basepage()['text']
  def addr(n):return base+sym[n]
  def stop():h.debug('b pc = $%x :once'%addr('WizzcatVis_FrameDone'),settle=.1)
  def step():
   h.stdin_cmd('b pc = $%x :once'%addr('WizzcatVis_FrameDone'),settle=.01)
   h.stdin_cmd('c',settle=.04)
  def dump(a,n):
   p=root/'analysis/temp-dump.bin';p.unlink(missing_ok=True)
   h.stdin_cmd('savebin %s $%x $%x'%(p,a,n),settle=.02)
   for _ in range(200):
    if p.exists() and p.stat().st_size==n:break
    time.sleep(.01)
   b=p.read_bytes();assert len(b)==n;p.unlink();return b
  def u16(n):return struct.unpack('>H',dump(addr(n),2))[0]
  def u32(n):return struct.unpack('>I',dump(addr(n),4))[0]
  stop();assert u16('gWizzcatVisReady')==1
  pcm=dump(u32('WIZfrontbuf'),2000)
  assert len(set(pcm))>4,'DMA ring contains no mixed audio'
  bgptr=struct.unpack('>I',dump(addr('gScreenClass')+12,4))[0]
  background=dump(bgptr,32000);pages=set();seen=[set() for _ in range(4)];checks=0
  def check():
   global checks
   ages=struct.unpack('>4H',dump(addr('gWizzcatVisAge'),8))
   levels=struct.unpack('>4H',dump(addr('gWizzcatVisLevel'),8))
   enabled=u16('gWizzcatVisEnabled');page=u16('gWizzcatVisPage')
   assert levels==tuple(16-a if enabled and a<16 else 0 for a in ages)
   assert all(a<=0x4000 for a in ages)
   assert struct.unpack('>4H',dump(addr('gWizzcatVisPrevious')+page*8,8))==levels
   want=bytearray(background)
   for i,level in enumerate(levels):
    seen[i].add(level)
    for x in ([48,208,256,96][i],):
     for y in range(150):
      off=(36+y)*160+x//16*8
      want[off:off+8]=frames[level*1200+y*8:level*1200+y*8+8]
   ptr=u32('gWizzcatVisScreen');pages.add(ptr)
   actual=dump(ptr,32000)
   assert actual==want,(version,levels,next((i,a,b) for i,(a,b) in enumerate(zip(actual,want)) if a!=b))
   checks+=1
  for i in range(24):check();step()
  # Observe sparse later notes rather than assume a fixed boot/song position.
  for batch in range(16):
   if all(len(s)>1 for s in seen):break
   h.stdin_cmd('c',settle=.04);h.wait(3);stop()
   for i in range(8):check();step()
  assert len(pages)==2 and all(len(s)>1 for s in seen),seen
  h.stdin_cmd('c',settle=.05);shot=h.screenshot()
  for key,variable,value in [('V','gWizzcatVisEnabled',0),('V','gWizzcatVisEnabled',1),('F1','gWizzcatVisRaster',1),('F1','gWizzcatVisRaster',0)]:
   h.tap(key);stop();assert u16(variable)==value
   for _ in range(3):check();step()
   h.stdin_cmd('c',settle=.04)
  h.tap('SPACE');h.wait(3)
  assert h.mem(addr('gWizzcatVisExited'),2).u16(addr('gWizzcatVisExited'))==1
  (root/('analysis/verification-'+version+'.log')).write_text('\n'.join(h.lines))
  faults=[l for l in h.lines if any(e in l for e in ['Bus Error','Address Error','Illegal instruction'])]
  results.append({'native_dma_pcm':True,'tos':version,'machine':'ste','cpu_mhz':8,'ram_mb':1,'full_screen_checks':checks,'both_pages':True,'activity_levels':[sorted(s) for s in seen],'controls':True,'app_cleanup_returned':True,'clean_tos_exit':not faults,'faults':faults,'screenshot':shot})
  (root/('analysis/verification-'+version+'.log')).write_text('\n'.join(h.lines))
  print(version,'PASS rendering/controls',checks,'complete pages',flush=True)
  (root/('analysis/results-'+version+'.json')).write_text(json.dumps(results[-1],indent=2)+'\n')
  assert not faults,faults
(root/'analysis/results.json').write_text(json.dumps(results,indent=2)+'\n')
