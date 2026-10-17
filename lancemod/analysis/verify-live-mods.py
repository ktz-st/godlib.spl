"""Live VBL/DMA smoke tests for the supplied MODs, using German TOS 1.62."""
from pathlib import Path
import os,sys,tempfile,shutil,json
os.environ['SDL_VIDEODRIVER']='dummy';sys.path.insert(0,str(Path.home()/'.agents/skills/hatari-debugging/scripts'))
from hatari_session import HatariSession,nm_symbols
root=Path(__file__).resolve().parents[1];sy=nm_symbols(str(root/'analysis/LMDBG.PRG'),nm='m68k-atari-mintelf-nm');results=[]
for module in ['LOSTPARO.MOD','BOOTUP.MOD','CANNONFO.MOD']:
 with tempfile.TemporaryDirectory(prefix='lance-live-') as td:
  d=Path(td);shutil.copyfile(root/'LANCEMOD.TOS',d/'LANCEMOD.TOS');shutil.copyfile(root/module,d/'LOSTPARO.MOD')
  with HatariSession(str(d/'LANCEMOD.TOS'),tos=str(Path.home()/'Atari/tos/TOS v1.62 (1990)(Atari Corp)(STE)(De).img'),debug_except='bus,address,illegal',extra_args=['--confirm-quit','false','--memsize','1','--cpuclock','8','--cpulevel','0','--monitor','rgb']) as h:
   h.wait(9);base=h.basepage()['text'];a=lambda n:base+sy[n]
   assert h.mem(a('gLanceVisReady'),2).u16(a('gLanceVisReady'))==1
   f=h.mem(a('gLanceVisFrames'),4).u32(a('gLanceVisFrames'));h.wait(2);f2=h.mem(a('gLanceVisFrames'),4).u32(a('gLanceVisFrames'));assert f2>f
   ages=h.mem(a('gLanceVisAge'),8);assert any(ages.u16(a('gLanceVisAge')+2*i)<0x4000 for i in range(4))
   missed=h.mem(a('gLanceVisMissedVbl'),4).u32(a('gLanceVisMissedVbl'))
   h.tap('SPACE');h.wait(3)
   assert h.mem(a('gLanceVisExited'),2).u16(a('gLanceVisExited'))==1
   dma=h.mem(0xff8901,1).u8(0xff8901);assert dma==0
   faults=[l for l in h.lines if any(e in l for e in ['Bus Error','Address Error','Illegal instruction'])];assert not faults,faults
   (root/('analysis/live-'+module+'.log')).write_text('\n'.join(h.lines))
   results.append({'module':module,'rate':'25 kHz','tos':'1.62 De','cpu_mhz':8,'ram_mb':1,'frames_advance':f2-f,'missed_vbl':missed,'clean_exit':True,'dma_stopped':True,'faults':faults})
   print(module,'PASS',results[-1],flush=True)
(root/'analysis/live-memory-results.json').write_text(json.dumps(results,indent=2)+'\n')
