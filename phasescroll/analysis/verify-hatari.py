"""Check scanwalk against the tile map, displayed pixels, raster timing and exit."""
from pathlib import Path
import json,os,struct,subprocess,sys,time
from PIL import Image
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
sys.path.insert(0,str(Path.home()/'.agents/skills/hatari-debugging/scripts'))
from hatari_session import HatariSession
from check_trace import check_trace
root=Path(__file__).resolve().parents[1]
sym={p[2]:int(p[0],16) for l in subprocess.check_output(['m68k-atari-mintelf-nm',str(root/'analysis/PDBG.PRG')],text=True).splitlines() if len(p:=l.split())==3}
tiles=(root/'assets/TDATA.BIN').read_bytes();level=(root/'assets/LMAP.BIN').read_bytes()
# A complete rectangular map strip; no scanwalk, phases or fill-gauge logic.
world=b''.join(tiles[level[(22+y//16)*144+x]*128+(y&15)*8:level[(22+y//16)*144+x]*128+(y&15)*8+8] for y in range(160) for x in range(144))
def viewport(raw,start,stride,fine,height=160):
 out=bytearray()
 for y in range(height):
  for x in range(20):
   a=start+y*stride+x*8
   if not fine:out.extend(raw[a:a+8])
   else:
    v=struct.unpack_from('>8H',raw,a)
    out.extend(struct.pack('>4H',*[((v[p]<<fine)|(v[p+4]>>(16-fine)))&65535 for p in range(4)]))
 return bytes(out)
def expected(x):return viewport(world,(x//16)*8,1152,x&15)
def decode(raw,palette):
 colours=[tuple((((v>>s)&7)*2+((v>>(s+3))&1))*17 for s in (8,4,0)) for v in palette]
 out=bytearray()
 for a in range(0,len(raw),8):
  words=struct.unpack_from('>4H',raw,a)
  for bit in range(15,-1,-1):out.extend(colours[sum(((words[p]>>bit)&1)<<p for p in range(4))])
 return bytes(out)
version='1.62' if '--tos162' in sys.argv else '2.06';tag='ste-'+version
rom='TOS v1.62 (1990)(Atari Corp)(STE)(GB)[STE TOS, Rev 2].img' if version=='1.62' else 'TOS v2.06 (1991)(Atari Corp)(Mega-STE)(UK).img'
trace=root/('analysis/video-'+tag+'.log')
with HatariSession(str(root/'PHASE.PRG'),machine='ste',sound=False,screenshot_dir=str(root/'analysis/shots'/tag/str(int(time.time()))),debug_except='bus,address,illegal',extra_args=['--tos',str(Path.home()/'Atari/tos'/rom),'--confirm-quit','false','--memsize','1','--cpuclock','8','--cpulevel','0','--monitor','rgb','--trace','video_ste,video_color','--trace-file',str(trace)]) as h:
 h.wait(8);base=h.basepage()['text']
 def addr(n):return base+sym[n]
 def stop():h.debug('b pc = $%x :once'%addr('Screen_Update'))
 def dump(a,size):
  p=root/('analysis/temp-'+tag+'.bin');p.unlink(missing_ok=True)
  h.stdin_cmd('savebin %s $%x $%x'%(p,a,size),settle=.04)
  for i in range(200):
   if p.exists() and p.stat().st_size==size:break
   time.sleep(.01)
  b=p.read_bytes();assert len(b)==size;p.unlink();return b
 def read(n,size):return dump(addr(n),size)
 def word(n):return struct.unpack('>H',read(n,2))[0]
 def write(n,v):h.stdin_cmd('w $%x $%02x $%02x'%(addr(n),(v&65535)>>8,v&255),settle=.03)
 def resume():h.stdin_cmd('c',settle=.04)
 def step():
  h.stdin_cmd('b pc = $%x :once'%addr('Screen_Update'),settle=.02);resume()
 stop();assert word('gPhaseReady')==1
 state=read('Phase_State',26);buffer=struct.unpack_from('>I',state)[0];tileptr=struct.unpack('>I',read('Phase_Tiles',4))[0]
 assert tileptr&65535==0 and buffer==tileptr+32768
 assert dump(tileptr,32768)==tiles
 screenstate=read('gScreenClass',42);panel=struct.unpack_from('>I',screenstate,12)[0]
 hud=dump(panel,6400);hudpal=struct.unpack('>16H',read('gHSplitHudPalette',32));pal=struct.unpack('>16H',read('Phase_Palette',32))
 positions=[];pixel_checks=[];fine=set();directions=set();magnitudes=set()
 def check():
  state=read('Phase_State',26);ptr=struct.unpack_from('>I',state,4)[0];x,speed,direction,fill,coarse,mapx,previous,y,mapy=struct.unpack_from('>9h',state,8)
  raw=dump(buffer,32768)
  assert 0<=x<=1984 and ptr==buffer+8+(x//16)*8 and mapx==x//16,(x,ptr,mapx)
  want=expected(x);actual=viewport(raw,ptr-buffer,184,x&15)
  if actual!=want:
   (root/('analysis/failure-'+tag+'.bin')).write_bytes(raw)
   raise AssertionError((tag,'map mismatch',x,speed,direction,fill,coarse,next((i,a,b) for i,(a,b) in enumerate(zip(actual,want)) if a!=b)))
  # Private bank stays inside its allocated 32K; the unused tail is a guard.
  assert not any(raw[30432:]),(tag,'scanwalk overflow')
  positions.append(x);fine.add(x&15);directions.add(1 if speed>0 else -1 if speed<0 else 0);magnitudes.add(abs(speed))
  return x
 def displayed():
  # Paused phase processing can continue filling its hidden update column.
  write('gPhaseMagnitude',0);resume();h.wait(.12);shot=h.screenshot();stop()
  x=word('gPhaseShownX');im=Image.open(shot).convert('RGB');assert im.size==(832,588),im.size
  actual=im.crop((96,58,736,458)).resize((320,200),Image.Resampling.NEAREST).tobytes()
  want=decode(hud,hudpal)+decode(expected(x),pal)
  assert actual==want,(tag,'display',x,next((i//3%320,i//960,a,b) for i,(a,b) in enumerate(zip(actual,want)) if a!=b),shot)
  assert dump(panel,6400)==hud;pixel_checks.append(x)
  return shot
 # Every fine phase in both directions, then disruptive speed/direction changes.
 for direction in [1,-1]:
  write('gPhaseDirection',direction);write('gPhaseMagnitude',1)
  for i in range(20):check();step()
 for i in range(64):
  speed=[1,8,2,4,0,8,1,2][i%8];direction=[1,-1,1,-1,1,1,-1,-1][i%8]
  write('gPhaseMagnitude',speed);write('gPhaseDirection',direction);step();check()
  if i%16==15:displayed();print(tag,'PASS changes',i+1,flush=True)
 # Reach both ends by scrolling normally; never teleport the core state.
 for direction,edge in [(-1,0),(1,1984),(-1,0)]:
  write('gPhaseDirection',direction);write('gPhaseMagnitude',8)
  for i in range(260):
   step();x=check()
   if x==edge:break
  else:raise AssertionError((tag,'edge not reached',edge,x))
  displayed();print(tag,'PASS edge',edge,flush=True)
 assert fine==set(range(16)) and directions=={-1,0,1} and magnitudes=={0,1,2,4,8}
 # Exercise the keyboard handlers, including Hatari's single-character "8"
 # (a padded scancode 09 is rejected as an invalid octal number by Hatari).
 resume()
 for key,speed in [('1',1),('2',2),('4',4),('8',8),('0',0)]:
  if key=='8':h.control('hatari-event keydown 8');h.wait(.15);h.control('hatari-event keyup 8')
  else:h.tap(key)
  stop();assert word('gPhaseMagnitude')==speed;resume()
 h.tap('LEFT');stop();assert word('gPhaseDirection')==65535;resume()
 h.tap('RIGHT');stop();assert word('gPhaseDirection')==1;resume()
 h.tap('SPACE');stop();assert word('gPhaseDirection')==65535;resume()
 h.tap('R');stop();assert word('gPhaseRaster')==1
 shot=displayed();missed=struct.unpack('>I',read('gPhaseMissedVbl',4))[0];assert missed==0,missed
 resume();h.control('hatari-event keydown 01');h.wait(.3);h.control('hatari-event keyup 01');h.wait(5)
 assert h.mem(addr('gPhaseExited'),2).u16(addr('gPhaseExited'))==1
 assert h.mem(addr('gScreenClass'),4).u32(addr('gScreenClass'))==0
 vector=h.mem(0x120,4).u32(0x120);assert not addr('HSplit_TimerB')<=vector<addr('HSplit_TimerBEnd')
 faults=[l for l in h.lines if any(e in l for e in ('Bus Error','Address Error','Illegal instruction'))];assert not faults,faults
 (root/('analysis/verification-'+tag+'.log')).write_text('\n'.join(h.lines))
 timing=check_trace(trace,addr('HSplit_TimerB'),addr('HSplit_TimerBEnd'),pal)
 result={'machine':'ste','tos':version,'cpu_mhz':8,'ram_mb':1,'map_comparisons':len(positions),'fine_phases':sorted(fine),'speeds':sorted(magnitudes),'directions':sorted(directions),'min_x':min(positions),'max_x':max(positions),'displayed_pixel_checked_x':pixel_checks,'hud_unchanged':True,'bank_alignment_and_guard':True,'missed_vbl':missed,'controls_and_exit':True,'screenshot':shot,**timing}
 (root/('analysis/results-'+tag+'.json')).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2),flush=True)
