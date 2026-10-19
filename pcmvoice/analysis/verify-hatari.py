from pathlib import Path
import json,subprocess,sys,time,os,shutil,tempfile
sys.path.insert(0,str(Path.home()/'.codex/skills/hatari-debugging/scripts'))
from hatari_session import HatariSession
root=Path(__file__).resolve().parent
exe=root/'PCMVODBG.PRG'
out=subprocess.check_output(['m68k-atari-mintelf-nm',str(exe)],text=True)
syms={p[2]:int(p[0],16) for l in out.splitlines() if len(p:=l.split())==3}
# Keep GEMDOS directory enumeration and 8.3 aliases independent of build files.
with tempfile.TemporaryDirectory(prefix='pcmvoice-hatari-') as run_dir:
 run_exe=Path(run_dir)/'PCMVOICE.PRG';shutil.copy2(exe,run_exe)
 with HatariSession(str(run_exe),machine='ste',sound=False,tos=os.environ.get('HATARI_TOS'),debug_except='bus,address,illegal',extra_args=['--confirm-quit','false','--memsize','4','--cpuclock','8']) as h:
  h.wait(15);base=h.basepage()['text']
  def integer(name,size=2):
   a=base+syms[name];m=h.mem(a,size);return m.u16(a) if size==2 else m.u32(a)
  assert integer('gPcmVoiceMixReady')==1
  assert integer('gPacmadVerifyFailures')==0
  assert integer('gPacmadVerifyCases')==491
  for key in ('F1','F2','F3'):h.tap(key,hold=.1)
  h.wait(18) # Cross the old 250-byte/50-Hz drift boundary with all loops active.
  assert integer('sUnderruns',4)==0
  a=base+syms['sChannels'];m=h.mem(a,60)
  assert all(m.u8(a+i*20+17) for i in range(3))
  h.tap('F9',hold=.1);h.wait(.3);h.tap('F9',hold=.1)
  h.tap('F6',hold=.1);h.wait(.2)
  m=h.mem(a,60);assert not any(m.u8(a+i*20+17) for i in range(3))
  h.tap('F5',hold=.1);h.wait(1.7)
  m=h.mem(a,60);assert not m.u8(a+17) # both queued 8192-byte sources ended
  h.tap('F4',hold=.1);h.wait(.9)
  m=h.mem(a,60);assert not any(m.u8(a+i*20+17) for i in range(3))
  h.control('hatari-event keydown 01');h.wait(.1);h.control('hatari-event keyup 01');h.wait(1)
  assert integer('gPcmVoiceMixExited')==1
  faults=[l for l in h.lines if 'Address Error' in l or 'Bus Error' in l or 'Illegal instruction' in l]
  assert not faults,faults
  result=dict(core_cases=491,failures=0,live_loops_seconds=18,underruns=0,queue=True,one_shots=True,stop=True,exit=True,machine='Hatari STE 8 MHz')
  (root/'results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
