"""Native DMA/rate/cleanup smoke test; build both debug variants first."""
import os,sys,json,time
from pathlib import Path
os.environ['SDL_VIDEODRIVER']='dummy';sys.path.insert(0,str(Path.home()/'.agents/skills/hatari-debugging/scripts'))
from hatari_session import HatariSession,nm_symbols
root=Path(__file__).resolve().parents[1];results=[]
for rate,program,debug,size in [(12,'LEO12.TOS','LEO12DBG.PRG',2032),(25,'LEONARD.TOS','LEODBG.PRG',4032)]:
 sy=nm_symbols(str(root/'analysis'/debug),nm='m68k-atari-mintelf-nm')
 with HatariSession(str(root/program),tos=str(Path.home()/'Atari/tos/TOS v1.62 (1990)(Atari Corp)(STE)(De).img'),debug_except='bus,address,illegal',extra_args=['--confirm-quit','false','--memsize','1','--cpuclock','8','--cpulevel','0']) as h:
  h.wait(10);base=h.basepage()['text'];addr=lambda n:base+sy[n]
  assert h.mem(addr('gLeonardVisReady'),2).u16(addr('gLeonardVisReady'))==1
  frames=h.mem(addr('gLeonardVisFrames'),4).u32(addr('gLeonardVisFrames'))
  workspace=h.mem(addr('sWorkspaceBytes'),4).u32(addr('sWorkspaceBytes'))
  assert workspace==(61134 if rate==12 else 91134)
  assert h.mem(0xffff8921,1).u8(0xffff8921)==(1 if rate==12 else 2)
  p=h.mem(addr('LeoSampleBuffer'),4).u32(addr('LeoSampleBuffer'))
  pcm=root/'analysis/temp-pcm.bin';pcm.unlink(missing_ok=True)
  h.debug('savebin %s $%x $%x'%(pcm,p,size))
  b=pcm.read_bytes();pcm.unlink();assert len(b)==size and len(set(b))>4
  h.wait(1)
  assert h.mem(addr('gLeonardVisFrames'),4).u32(addr('gLeonardVisFrames'))>frames
  h.tap('SPACE');h.wait(2)
  assert h.mem(addr('gLeonardVisExited'),2).u16(addr('gLeonardVisExited'))==1
  assert h.mem(0xff8901,1).u8(0xff8901)==0
  assert h.mem(addr('sWorkspaceBytes'),4).u32(addr('sWorkspaceBytes'))==0
  faults=[l for l in h.lines if any(e in l for e in ['Bus Error','Address Error','Illegal instruction'])]
  (root/('analysis/audio-smoke-%d.log'%rate)).write_text('\n'.join(h.lines))
  assert not faults,faults
  result=dict(rate_khz=rate,workspace_bytes=workspace,pcm_values=len(set(b)),frames_at_capture=frames,native_dma=True,workspace_freed=True,clean_exit=True,tos='1.62-de')
  results.append(result);print(result,flush=True)
(root/'analysis/audio-smoke-results.json').write_text(json.dumps(results,indent=2)+'\n')
