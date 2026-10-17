"""hrdb 68000 instruction-cycle profile. Same driver for baseline and optimized."""
from pathlib import Path
import bisect,json,os,subprocess,sys,time
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
sys.path.insert(0,str(Path.home()/'.codex/skills/hatari-debugging/scripts'))
from hatari_session import HatariSession
from hrdb_profile import Rdb,profile_lines,nm_symbols
root=Path(__file__).resolve().parents[1]
label=sys.argv[1] if len(sys.argv)>1 else 'baseline'
prog=root/('analysis/BASE.PRG' if label=='baseline' else 'SNOW.PRG')
symbols=root/('analysis/BASESY.PRG' if label=='baseline' else 'analysis/SDBG.PRG')
syms=nm_symbols(str(symbols));sd=dict((n,a) for a,n in syms);sa=[a for a,n in syms]
rom='/Users/kriss/Atari/tos/TOS v2.06 (1991)(Atari Corp)(Mega-STE)(UK).img'
with HatariSession(str(prog),hatari='hatari-hrdb',machine='st',sound=False,extra_args=['--tos',rom,'--confirm-quit','false','--memsize','1','--cpulevel','0','--cpuclock','8','--monitor','rgb']) as h:
 h.wait(8);base=h.basepage()['text']
 r=Rdb();r.cmd('break',wait=1);r.cmd('profile 1');r.cmd('run');start=time.monotonic();h.wait(6);r.cmd('break',wait=2);elapsed=time.monotonic()-start
 msg=r.take('!profile');assert msg,'No profile notification';lines=profile_lines(msg);assert lines
 entries={a-base:(n,c) for a,n,c in lines}
 agg={};total=sum(c for a,n,c in lines)
 for a,n,c in lines:
  rel=a-base
  if 0<=rel<=sa[-1]:
   idx=bisect.bisect_right(sa,rel)-1;name=syms[idx][1]
  else:name='TOS/interrupts' if a>=0xe00000 else 'other'
  agg[name]=agg.get(name,0)+c
 def region(start,size):return sum(c for a,n,c in lines if base+start<=a<base+start+size)
 snowstart=sd['Snow_Step'];snowend=sd.get('Snow_StepEnd',sd['Snow_Background'])
 copy=sd.get('Snow_Present',sd['Graphic_4BP_CopyScreen'])
 copyend=sd.get('Snow_PresentEnd')
 if copyend is None:
  copyend=next(a for a,n in syms if a>copy and n.startswith('Graphic_') and not n.startswith('Graphic_4BP_CopyScreen'))
 calls=entries.get(snowstart,(0,0))[0];assert calls>0
 result={'label':label,'total_cycles':total,'snow_calls':calls,'snow_cycles':region(snowstart,snowend-snowstart),'copy_calls':entries.get(copy,(0,0))[0],'copy_cycles':region(copy,copyend-copy),'elapsed_wall_seconds':elapsed,'top_symbols':sorted(agg.items(),key=lambda p:-p[1])[:25]}
 result['snow_cycles_per_call']=result['snow_cycles']/calls
 result['copy_cycles_per_call']=result['copy_cycles']/max(1,result['copy_calls'])
 (root/('analysis/profile-'+label+'.json')).write_text(json.dumps(result,indent=2)+'\n')
 (root/('analysis/profile-'+label+'-addresses.json')).write_text(json.dumps([(a-base,n,c) for a,n,c in lines]))
 print(json.dumps(result,indent=2),flush=True);r.cmd('profile 0');r.cmd('run');r.s.close()
