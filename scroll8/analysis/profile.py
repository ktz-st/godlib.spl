"""Shared 320x8 viewport/font/text, speed 2, optimized Griff and original MCoder."""
from pathlib import Path
import json,os,subprocess,sys
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
sys.path.insert(0,str(Path.home()/'.agents/skills/hatari-debugging/scripts'))
from hatari_session import HatariSession
from hrdb_profile import Rdb,profile_lines
root=Path(__file__).resolve().parents[1]
sym={p[2]:int(p[0],16) for l in subprocess.check_output(['m68k-atari-mintelf-nm',str(root/'analysis/S8DBG.PRG')],text=True).splitlines() if len(p:=l.split())==3}
rom=Path.home()/'Atari/tos/TOS v2.06 (1991)(Atari Corp)(Mega-STE)(UK).img'
results=[]
for mode in [3,1,2]:
 with HatariSession(str(root/'SCROLL8.PRG'),hatari='hatari-hrdb',machine='st',sound=False,extra_args=['--tos',str(rom),'--confirm-quit','false','--memsize','1','--cpuclock','8','--cpulevel','0','--monitor','rgb']) as h:
  h.wait(8);base=h.basepage()['text'];h.tap(str(mode));h.wait(1)
  a=base+sym['gTinyMode'];assert h.mem(a,2).u16(a)==mode
  def sample():
   a=base+min(sym['gTinyLastVbl'],sym['gTinyFrames']);b=base+max(sym['gTinyLastVbl'],sym['gTinyFrames'])+4;m=h.mem(a,b-a)
   return m.u32(base+sym['gTinyLastVbl']),m.u32(base+sym['gTinyFrames'])
  v0,f0=sample();db=Rdb();db.cmd('break',wait=2);db.cmd('profile 1');db.cmd('run');h.wait(4);db.cmd('break',wait=4)
  msg=db.take('!profile');assert msg;lines=profile_lines(msg);assert lines
  def calls(n):return sum(nc for a,nc,c in lines if a==base+sym[n])
  def cost(first,last):return sum(c for a,n,c in lines if base+sym[first]<=a<base+sym[last])
  data=[]
  for kernel,flag in [('MCoder',1),('Griff',2)]:
   count=calls(kernel+'_Update');assert (count>100)==bool(mode&flag),(kernel,count,mode)
   if not count:continue
   assert abs(count-calls(kernel+'_Copy'))<=1
   update=cost(kernel+'_Update',kernel+'_UpdateEnd')/count
   copy=cost(kernel+'_Copy',kernel+'_CopyEnd')/count
   data.append({'kernel':kernel,'calls':count,'update_cycles':update,'copy_cycles':copy,'cycles_per_frame':update+copy,'ms':(update+copy)/8000,'pal_frame_percent':100*(update+copy)/160256})
  (root/('analysis/profile-raw-mode'+str(mode)+'.json')).write_text(json.dumps({'base':base,'lines':lines}))
  db.cmd('profile 0');db.cmd('run');v1,f1=sample();db.s.close()
  result={'mode':mode,'machine':'st','tos':'2.06','cpu_mhz':8,'ram_mb':1,'speed_pixels':2,'width':320,'height':8,'bitplanes':1,'updates_per_second_from_vbl_counters':50*(f1-f0)/(v1-v0),'kernels':data}
  results.append(result);print(json.dumps(result,indent=2),flush=True)
(root/'analysis/profile.json').write_text(json.dumps(results,indent=2)+'\n')
