"""Fresh hrdb process per count. Kernel cycles include generated pixel routines."""
from pathlib import Path
import json,os,subprocess,sys
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
sys.path.insert(0,str(Path.home()/'.codex/skills/hatari-debugging/scripts'))
from hatari_session import HatariSession
from hrdb_profile import Rdb,profile_lines
root=Path(__file__).resolve().parents[1]
sym={p[2]:int(p[0],16) for l in subprocess.check_output(['m68k-atari-mintelf-nm',str(root/'analysis/SDBG.PRG')],text=True).splitlines() if len(p:=l.split())==3}
results=[]
for key,count in [('1',96),('2',192),('3',384),('4',768)]:
 with HatariSession(str(root/'STARS.PRG'),hatari='hatari-hrdb',machine='st',sound=False,extra_args=['--tos',str(Path.home()/'Atari/tos/TOS v2.06 (1991)(Atari Corp)(Mega-STE)(UK).img'),'--confirm-quit','false','--memsize','1','--cpuclock','8','--cpulevel','0','--monitor','rgb']) as h:
  h.wait(16);base=h.basepage()['text'];h.tap(key);h.wait(2);r=Rdb()
  def sample():
   first=min(sym['gStarsLastVbl'],sym['gStarsFrames']);m=h.mem(base+first,8)
   return m.u32(base+sym['gStarsLastVbl']),m.u32(base+sym['gStarsFrames'])
  v0,f0=sample()
  r.cmd('break',wait=2);r.cmd('profile 1');r.cmd('run');h.wait(4);r.cmd('break',wait=4)
  msg=r.take('!profile')
  if not msg:
   r.pump(3);msg=r.take('!profile')
  if not msg:print('RDB messages',[(m[:4],len(m)) for m in r.msgs], 'Hatari log',h.lines[-15:],flush=True)
  assert msg;lines=profile_lines(msg);assert lines
  def cost(first,last):return sum(c for a,n,c in lines if base+sym[first]<=a<base+sym[last])
  def calls(name):return sum(n for a,n,c in lines if a==base+sym[name])
  draws=calls('Stars_Draw');erases=calls('Stars_Erase');assert draws>0 and erases>0
  (root/('analysis/profile-raw-'+str(count)+'.json')).write_text(json.dumps({'base':base,'draw_calls':draws,'erase_calls':erases,'lines':lines}))
  draw=(cost('Stars_Draw','Stars_DrawEnd')+cost('Stars_Code','Stars_CodeEnd'))/draws
  erase=cost('Stars_Erase','Stars_EraseEnd')/erases
  r.cmd('profile 0');r.cmd('run');v1,f1=sample();assert v1>v0 and f1>f0
  results.append({'stars':count,'draw_calls':draws,'erase_calls':erases,'draw_cycles_per_call':draw,'erase_cycles_per_call':erase,'total_kernel_cycles_per_frame':draw+erase,'kernel_ms_at_8mhz':(draw+erase)/8000,'kernel_percent_of_pal_frame':100*(draw+erase)/160256,'vbl_delta':v1-v0,'frame_delta':f1-f0,'updates_per_second_from_vbl_counters':50*(f1-f0)/(v1-v0)})
  r.s.close();print(json.dumps(results[-1],indent=2),flush=True)
(root/'analysis/profile.json').write_text(json.dumps(results,indent=2)+'\n')
