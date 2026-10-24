from pathlib import Path
import sys,os,time,json,tempfile
os.environ['SDL_VIDEODRIVER']='dummy';os.environ['SDL_AUDIODRIVER']='dummy'
sys.path.insert(0,'/Users/kriss/.agents/skills/hatari-debugging/scripts')
from hatari_session import HatariSession,nm_symbols
app=Path(__file__).resolve().parents[1];cfg=json.loads((app/'source/config.json').read_text());dbg='/tmp/DCKHDBG.PRG'if cfg['lanes']==1 else'/tmp/DCKMDBG.PRG';r=Path(tempfile.mkdtemp(prefix=app.name+'-controls-'));sy=nm_symbols(dbg,nm='m68k-atari-mintelf-nm')
with HatariSession(dbg,hatari='/opt/homebrew/opt/hatari/Hatari.app/Contents/MacOS/hatari',tos='/Users/kriss/Atari/tos/TOS v1.62 (1990)(Atari Corp)(STE)(De).img',machine='ste',extra_args=['--confirm-quit','false','--memsize','4','--cpulevel','0','--cpuclock','8','--fast-forward','true'])as h:
 h.wait(3);base=h.basepage()['text'];a=lambda n:base+sy[n]
 def data(n,size):
  p=r/'control.bin';p.unlink(missing_ok=True);h.debug(f'savebin {p} ${a(n):x} ${size:x}',settle=.1)
  for _ in range(50):
   if p.exists()and p.stat().st_size==size:return p.read_bytes()
   time.sleep(.01)
  raise RuntimeError(n)
 def val(n,size=2):return int.from_bytes(data(n,size),'big')
 assert val('gHSReady')==1
 f0=val('gHSFrames',4);m0=val('gHSMissedVbl',4);h.wait(3);f1=val('gHSFrames',4);m1=val('gHSMissedVbl',4)
 result={'frames':f1-f0,'missed_vbls':m1-m0,'estimated_fps':50*(f1-f0)/(f1-f0+m1-m0),'controls':{}}
 for count in range(1,cfg['lanes']+1):
  key=str(count)
  h.tap(key,hold=.06);h.wait(.1);v=val('gHSCount');assert v==count,(key,v);result['controls'][key]=v
 h.tap('SPACE',hold=.06);h.wait(.1);assert val('gHSPaused')==1;s0=data('gHSState',cfg['lanes']*24);h.wait(.3);s1=data('gHSState',cfg['lanes']*24);assert s0==s1;result['controls']['pause_freezes_state']=True
 h.tap('SPACE',hold=.06);h.wait(.3);assert val('gHSPaused')==0
 result['controls']['resumed']=True
 h.control('hatari-event keydown 01');h.wait(.1);h.control('hatari-event keyup 01');h.wait(.2);assert val('gHSExited')==1;result['controls']['exit']=True
 (Path(__file__).resolve().parents[1]/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(result,flush=True)
