"""HRDB cycle costs for the shipped WEDGES.PRG, same STE in both backends.
Costs include CPU stalls and polling while the shared-bus blitter runs.
VBL, input, Screen_Update and animation control outside Wedges_Render excluded.
"""
from pathlib import Path
import os,sys,json,hashlib,subprocess,re
os.environ.setdefault('SDL_VIDEODRIVER','dummy');os.environ.setdefault('SDL_AUDIODRIVER','dummy')
sys.path.insert(0,str(Path.home()/'.agents/skills/hatari-debugging/scripts'))
from hatari_session import HatariSession,nm_symbols
from hrdb_profile import Rdb,profile_lines
root=Path(__file__).resolve().parents[1];debug=root/'analysis/WEDGESDBG.PRG'
sym=nm_symbols(str(debug),nm='m68k-atari-mintelf-nm')
listing=subprocess.check_output(['m68k-atari-mintelf-objdump','-d','--disassemble=Wedges_Copy',str(debug)],text=True)
def instruction(fragment):
 for line in listing.splitlines():
  if fragment in line.replace(' ','').replace('\t',''):
   m=re.match(r'\s*([0-9a-f]+):',line)
   if m:return int(m[1],16)
 raise AssertionError(fragment)
normal=instruction('movew%a0@+,%a1@(');inverse=instruction('movew%a0@+,%d0');blit=instruction('movel%a2,%sp@-')
assert sym['Wedges_Copy']<normal<inverse<blit<sym['Wedges_CopyEnd']
results=[]
for backend in ('blitter','CPU'):
 with HatariSession(str(root/'WEDGES.PRG'),hatari='hatari-hrdb',tos=str(Path.home()/'Atari/tos/TOS v1.62 (1990)(Atari Corp)(STE)(De).img'),machine='ste',sound=False,extra_args=['--confirm-quit','false','--memsize','1','--cpuclock','8','--cpulevel','0','--monitor','rgb'])as h:
  h.wait(9);base=h.basepage()['text'];a=lambda n:base+sym[n]
  if backend=='CPU':h.tap('B')
  assert h.mem(a('gWedgesBlitter'),2).u16(a('gWedgesBlitter'))==(backend=='blitter')
  r=Rdb();r.cmd('break',wait=1);r.cmd('profile 1');r.cmd('run');h.wait(8);r.cmd('break',wait=2)
  msg=r.take('!profile')
  if not msg:r.pump(2);msg=r.take('!profile')
  data=profile_lines(msg);assert data
  rows={pc:(n,c)for pc,n,c in data}
  calls=lambda name:rows.get(a(name),(0,0))[0]
  cost=lambda start,end:sum(c for pc,n,c in data if base+start<=pc<base+end)
  rendered=calls('Wedges_Render');copied=calls('Wedges_Copy');assert rendered>256 and copied>256
  kernel=cost(sym['Wedges_Copy'],sym['Wedges_CopyEnd']);controller=cost(sym['Wedges_Render'],sym['Wedges_RenderEnd'])
  item={'backend':backend,'rendered_frames':rendered,'bitplane_copies':copied,'copies_per_rendered_frame':copied/rendered,'copy_cycles_per_call':kernel/copied,'copy_ms_per_call_at_8mhz':kernel/copied/8000,'render_controller_cycles_per_frame':controller/rendered,'total_renderer_cycles_per_frame':(kernel+controller)/rendered,'total_renderer_ms_per_frame':(kernel+controller)/rendered/8000,'total_renderer_percent_of_160000_cycle_frame':(kernel+controller)/rendered/1600}
  if backend=='CPU':
   n=rows.get(base+normal,(0,0))[0]/200;i=rows.get(base+inverse,(0,0))[0]/200;assert n>50 and i>50
   common=cost(sym['Wedges_Copy'],normal)/copied
   item['normal_copy_equivalents']=n;item['inverse_copy_equivalents']=i
   item['normal_copy_cycles']=common+cost(normal,inverse)/n
   item['inverse_copy_cycles']=common+cost(inverse,blit)/i
   item['balanced_full_rotation_copy_cycles']=(item['normal_copy_cycles']+item['inverse_copy_cycles'])/2
   item['balanced_full_rotation_renderer_percent']=(item['balanced_full_rotation_copy_cycles']*copied/rendered+controller/rendered)/1600
  r.cmd('profile 0');r.cmd('run');r.s.close()
  results.append(item);print(json.dumps(item,indent=2),flush=True)
report={'program_sha256':hashlib.sha256((root/'WEDGES.PRG').read_bytes()).hexdigest(),'configuration':'STE, 68000, 8 MHz, 1 MiB, PAL RGB, German TOS 1.62','method':'Fresh hatari-hrdb session per backend, default speed 6, 8-second sample wait plus protocol settling (>one full turn). Instruction-cycle sums for Wedges_Render and Wedges_Copy. Includes shared-bus blitter stalls/polling, excludes VBL/input/Screen_Update and animation update. Percent uses nominal 160000 cycles at 8 MHz / 50 Hz. CPU normal/inverse body costs separately measured and equally weighted for the balanced complete-rotation figure; actual window mean also retained.','frame_cache_bytes':256000,'results':results}
(root/'analysis/profile.json').write_text(json.dumps(report,indent=2)+'\n')
print('PASS profiling both backends',flush=True)
