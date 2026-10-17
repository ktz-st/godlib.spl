"""Run original 68000 bytes AND the GodLib port on patterned screens in Hatari."""
from pathlib import Path
import json,os,subprocess,sys
os.environ.setdefault('SDL_VIDEODRIVER','dummy');sys.path.insert(0,str(Path.home()/'.codex/skills/hatari-debugging/scripts'))
from hatari_session import HatariSession
r=Path(__file__).resolve().parents[1]
sym={p[2]:int(p[0],16) for l in subprocess.check_output(['m68k-atari-mintelf-nm',str(r/'analysis/ORACLE.PRG')],text=True).splitlines() if len(p:=l.split())==3}
with HatariSession(str(r/'analysis/ORACLE.PRG'),machine='st',sound=False,debug_except='bus,address,illegal',extra_args=['--tos',str(Path.home()/'Atari/tos/TOS v2.06 (1991)(Atari Corp)(Mega-STE)(UK).img'),'--confirm-quit','false','--memsize','1','--cpulevel','0','--cpuclock','8','--monitor','rgb','--fast-forward','true']) as h:
 h.wait(15);base=h.basepage()['text']
 def get(n,size=2):
  a=base+sym[n];m=h.mem(a,size);return m.u16(a) if size==2 else m.u32(a)
 result={n:get(n,4 if n in ('gOracleCompared','gOracleOffset') else 2) for n in ('gOracleDone','gOracleFailure','gOracleCase','gOracleTick','gOracleCompared','gOracleOffset')}
 print('oracle',result,flush=True)
 if result['gOracleDone']!=1:print('\n'.join(h.lines[-50:]),flush=True)
 assert result['gOracleDone']==1 and result['gOracleFailure']==0 and result['gOracleCompared']==400,result
 result.update({'machine':'st','cpu_mhz':8,'ram_mb':1,'tos':'2.06','cases':10,'calls_per_case':40,'bytes_compared_per_call':32000,'state_compared':True,'original_code_exit_patch':'TEXT $16fc: 41f9 -> 4e75 (STOS exit to RTS)'})
 (r/'analysis/original-results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
