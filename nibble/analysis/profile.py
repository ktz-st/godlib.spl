"""Instruction-cycle costs; exclude Screen_Update/VBL waits and startup prefill."""
from pathlib import Path
import json,os,subprocess,sys
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
sys.path.insert(0,str(Path.home()/'.agents/skills/hatari-debugging/scripts'))
from hatari_session import HatariSession
from hrdb_profile import Rdb,profile_lines
root=Path(__file__).resolve().parents[1]
sym={p[2]:int(p[0],16) for l in subprocess.check_output(['m68k-atari-mintelf-nm',str(root/'analysis/NDBG.PRG')],text=True).splitlines() if len(p:=l.split())==3}
rom=Path.home()/'Atari/tos/TOS v2.06 (1991)(Atari Corp)(Mega-STE)(UK).img'
results=[]
for name,keys in [('wave-1',[]),('wave-2',['2']),('flat',['3']),('paused',['SPACE']),('flat-paused',['3','SPACE'])]:
 with HatariSession(str(root/'NIBBLE.PRG'),hatari='hatari-hrdb',machine='st',sound=False,extra_args=['--tos',str(rom),'--confirm-quit','false','--memsize','1','--cpulevel','0','--cpuclock','8','--monitor','rgb']) as h:
  h.wait(8);base=h.basepage()['text']
  for key in keys:h.tap(key)
  h.wait(1)
  def sample():
   a=base+min(sym['gNibbleLastVbl'],sym['gNibbleFrames']);b=base+max(sym['gNibbleLastVbl'],sym['gNibbleFrames'])+4
   m=h.mem(a,b-a)
   return m.u32(base+sym['gNibbleLastVbl']),m.u32(base+sym['gNibbleFrames'])
  v0,f0=sample();db=Rdb();db.cmd('break',wait=2);db.cmd('profile 1');db.cmd('run');h.wait(4);db.cmd('break',wait=4)
  msg=db.take('!profile');assert msg;lines=profile_lines(msg);assert lines
  def calls(n):return sum(count for a,count,c in lines if a==base+sym[n])
  def cost(first,last):return sum(c for a,n,c in lines if base+sym[first]<=a<base+sym[last])
  frames=calls('Nibble_Draw')+calls('Nibble_DrawFlat');assert frames>100,frames
  advance=cost('Nibble_Advance','Nibble_AdvanceEnd')/frames
  shift=cost('Nibble_Shift','Nibble_ShiftEnd')/frames
  draw=(cost('Nibble_Draw','Nibble_DrawEnd')+cost('Nibble_DrawFlat','Nibble_DrawFlatEnd'))/frames
  clear=cost('Nibble_Clear','Nibble_ClearEnd')/frames
  assert calls('Nibble_Clear')==0,'startup/wave-switch cost leaked into steady state'
  assert (calls('Nibble_Advance')>100)==('paused' not in name)
  (root/('analysis/profile-raw-'+name+'.json')).write_text(json.dumps({'base':base,'lines':lines,'draw_calls':frames}))
  db.cmd('profile 0');db.cmd('run');v1,f1=sample();db.s.close()
  result={'mode':name,'machine':'st','tos':'2.06','cpu_mhz':8,'ram_mb':1,'draw_calls':frames,'advance_calls':calls('Nibble_Advance'),'advance_cycles_per_frame':advance,'shift_cycles_per_frame':shift,'draw_cycles_per_frame':draw,'kernel_cycles_per_frame':advance+draw+clear,'kernel_ms':(advance+draw+clear)/8000,'pal_frame_budget_percent':100*(advance+draw+clear)/160256,'vbl_delta':v1-v0,'frame_delta':f1-f0,'updates_per_second_from_vbl_counters':50*(f1-f0)/(v1-v0)}
  results.append(result);print(json.dumps(result,indent=2),flush=True)
(root/'analysis/profile.json').write_text(json.dumps(results,indent=2)+'\n')
