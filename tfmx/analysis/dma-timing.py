#!/usr/bin/env python3
"""Regression for DMA-start jitter: variable-cost work must follow DMA start."""
from pathlib import Path
import sys,os,tempfile,shutil,re,json,hashlib
sys.path.insert(0,str(Path.home()/'.agents/skills/hatari-debugging/scripts'))
from hatari_session import HatariSession,nm_symbols
os.environ['SDL_VIDEODRIVER']='dummy';os.environ['SDL_AUDIODRIVER']='dummy'
root=Path(__file__).resolve().parents[1];sy=nm_symbols(str(root/'analysis/TFMXDBG.PRG'),nm='m68k-atari-mintelf-nm')
release_hash=hashlib.sha256((root/'TFMX.PRG').read_bytes()).hexdigest()
with tempfile.TemporaryDirectory() as td:
 p=Path(td);trace=p/'dma.trace';shutil.copy(root/'TFMX.PRG',p/'TFMX.PRG')
 for x in list(root.glob('*.SMP'))+list(root.glob('*.MDT')):shutil.copy(x,p/x.name)
 with HatariSession(str(p/'TFMX.PRG'),hatari='/opt/homebrew/opt/hatari/Hatari.app/Contents/MacOS/hatari',tos=str(Path.home()/'Atari/tos/TOS v1.62 (1990)(Atari Corp)(STE)(De).img'),sound=False,extra_args=['--confirm-quit','false','--memsize','4','--trace-file',str(trace)]) as h:
  h.wait(9);base=h.basepage()['text']
  for _ in range(100):
   f=p/'ready';h.debug(f'savebin {f} ${base+sy["gTfmxReady"]:x} 2',settle=.1)
   if f.exists() and f.read_bytes()==b'\0\1':break
   h.wait(.2)
  assert f.exists() and f.read_bytes()==b'\0\1', 'player did not become ready'
  h.control('hatari-option --trace dmasound',settle=.1);h.wait(15);h.control('hatari-option --trace none',settle=.1)
 text=trace.read_text()
cycles=[int(x) for x in re.findall(r'DMA snd control write: 0x0001 video_cyc=(\d+)',text)]
r={'frames':len(cycles),'min_start_cycle':min(cycles),'max_start_cycle':max(cycles),'max_adjacent_jitter_cycles':max(abs(b-a)for a,b in zip(cycles,cycles[1:])),'start_cycles':cycles}
r['release_sha256']=release_hash
r['machine']='STE 68000 8MHz PAL, German TOS 1.62'
r['method']='15 seconds of DMA register-write trace after the title becomes ready; video cycles of DMA start, not host wall time.'
r['result']='PASS' if len(cycles)>500 and r['max_adjacent_jitter_cycles']<8000 else 'FAIL'
(root/'analysis/dma-timing.json').write_text(json.dumps(r,indent=2)+'\n')
print({k:v for k,v in r.items()if k!='start_cycles'},flush=True)
assert r['result']=='PASS',r
