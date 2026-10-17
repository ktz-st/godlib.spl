"""HRDB kernel profile, excluding VBL/input and the optional raster wait."""
from pathlib import Path
import json,os,subprocess,sys
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
sys.path.insert(0,str(Path.home()/'.agents/skills/hatari-debugging/scripts'))
from hatari_session import HatariSession
from hrdb_profile import Rdb,profile_lines
root=Path(__file__).resolve().parents[1]
sym={p[2]:int(p[0],16) for l in subprocess.check_output(['m68k-atari-mintelf-nm',str(root/'analysis/TCHDB.PRG')],text=True).splitlines() if len(p:=l.split())==3}
rom=Path.home()/'Atari/tos/TOS v2.06 (1991)(Atari Corp)(Mega-STE)(UK).img'
results=[]
for mode in ['mouse', 'auto']:
 with HatariSession(str(root/'TORCH.PRG'),hatari='hatari-hrdb',machine='st',sound=False,extra_args=['--tos',str(rom),'--confirm-quit','false','--memsize','1','--cpuclock','8','--cpulevel','0','--monitor','rgb']) as h:
  h.wait(8);base=h.basepage()['text']
  if mode=='auto':h.tap('A');h.wait(.3)
  def sample():
   a=base+min(sym['gFxLastVbl'],sym['gFxFrames']);b=base+max(sym['gFxLastVbl'],sym['gFxFrames'])+4;m=h.mem(a,b-a)
   return m.u32(base+sym['gFxLastVbl']),m.u32(base+sym['gFxFrames'])
  v0,f0=sample();db=Rdb();db.cmd('break',wait=2);db.cmd('profile 1');db.cmd('run');h.wait(6);db.cmd('break',wait=4)
  msg=db.take('!profile');assert msg;lines=profile_lines(msg);assert lines
  calls=sum(n for a,n,c in lines if a==base+sym['Torch_Render']);assert calls>100
  data=[]
  for kernel in ['Torch_Render', 'Torch_Clear', 'Torch_Draw', 'Torch_Record']:
   assert sym[kernel]<sym[kernel+'End']
   count=sum(n for a,n,c in lines if a==base+sym[kernel]);assert abs(count-calls)<=1,(kernel,count,calls)
   cost=sum(c for a,n,c in lines if base+sym[kernel]<=a<base+sym[kernel+'End'])/calls
   data.append({'kernel':kernel,'calls':count,'cycles_per_frame':cost,'ms':cost/8000,'pal_frame_percent':100*cost/160256})
  (root/('analysis/profile-raw-'+mode+'.json')).write_text(json.dumps({'base':base,'lines':lines}))
  db.cmd('profile 0');db.cmd('run');v1,f1=sample();db.s.close()
  cycles=sum(d['cycles_per_frame'] for d in data)
  result={'mode':mode,'machine':'st','tos':'2.06','cpu_mhz':8,'ram_mb':1,'kernel_costs':data,'cycles_per_frame':cycles,'ms':cycles/8000,'pal_frame_percent':100*cycles/160256,'updates_per_second_from_vbl':50*(f1-f0)/(v1-v0)}
  results.append(result);print(json.dumps(result,indent=2),flush=True)
(root/'analysis/profile.json').write_text(json.dumps(results,indent=2)+'\n')
