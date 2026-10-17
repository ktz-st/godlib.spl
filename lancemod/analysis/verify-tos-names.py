"""Run identical LM.TOS bytes on GB and German TOS 1.62; verify clean exit."""
import os,sys,shutil,json,time,tempfile
from pathlib import Path
os.environ['SDL_VIDEODRIVER']='dummy'
sys.path.insert(0,str(Path.home()/'.agents/skills/hatari-debugging/scripts'))
from hatari_session import HatariSession,nm_symbols
root=Path(__file__).resolve().parents[1]
a=Path(tempfile.mkdtemp(prefix='lance-short-name-'))
for src,dst in [('LANCEMOD.TOS','LM.TOS'),('LOSTPARO.MOD','LOSTPARO.MOD')]:shutil.copyfile(root/src,a/dst)
sym=nm_symbols(str(root/'analysis/LMDBG.PRG'),nm='m68k-atari-mintelf-nm')
results=[]
for tag,rom in [('gb','TOS v1.62 (1990)(Atari Corp)(STE)(GB)[STE TOS, Rev 2].img'),('de','TOS v1.62 (1990)(Atari Corp)(STE)(De).img')]:
 with HatariSession(str(a/'LM.TOS'),tos=str(Path.home()/'Atari/tos'/rom),debug_except='bus,address,illegal',screenshot_dir=str(root/'analysis/shots'/('short-'+tag)),extra_args=['--confirm-quit','false','--memsize','1','--cpuclock','8','--cpulevel','0','--monitor','rgb']) as h:
  h.wait(9);base=h.basepage()['text'];addr=lambda n:base+sym[n]
  assert h.mem(addr('gLanceVisReady'),2).u16(addr('gLanceVisReady'))==1
  before=h.mem(addr('gLanceVisFrames'),4).u32(addr('gLanceVisFrames'));h.wait(1)
  after=h.mem(addr('gLanceVisFrames'),4).u32(addr('gLanceVisFrames'));assert after>before
  assert not any('Bus Error' in l for l in h.lines)
  h.tap('SPACE');h.wait(3)
  exited=h.mem(addr('gLanceVisExited'),2).u16(addr('gLanceVisExited'))==1
  shot=h.screenshot()
  faults=[l for l in h.lines if any(e in l for e in ['Bus Error','Address Error','Illegal instruction'])]
  (root/('analysis/short-name-'+tag+'.log')).write_text('\n'.join(h.lines))
  results.append({'rom':rom,'program':'LM.TOS','frames_advance':True,'app_cleanup_returned':exited,'clean_tos_exit':not faults,'faults':faults,'screenshot':shot})
  print(tag,results[-1],flush=True)
(root/'analysis/name-results.json').write_text(json.dumps(results,indent=2)+'\n')
shutil.rmtree(a)
