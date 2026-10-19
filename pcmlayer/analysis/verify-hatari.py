import os,sys,time,json,subprocess
from pathlib import Path
sys.path.insert(0,str(Path.home()/'.codex/skills/hatari-debugging/scripts'))
from hatari_session import HatariSession
root=Path(__file__).resolve().parents[1]
nm=subprocess.check_output(['m68k-atari-mintelf-nm','-n',str(root/'analysis/PCMLYDBG.PRG')],text=True)
syms={l.split()[2]:int(l.split()[0],16) for l in nm.splitlines() if len(l.split())==3}
with HatariSession(str(root/'PCMLAYER.PRG'),screenshot_dir=str(root/'analysis/shots'),sound=False,tos=os.environ.get('HATARI_TOS'),debug_except='bus,address,illegal',extra_args=['--confirm-quit','false','--memsize','4','--monitor','rgb']) as h:
 h.wait(7)
 base=h.basepage();print('basepage',base,flush=True)
 a=lambda n:base['text']+syms[n]
 assert h.mem(a('gPcmLayerMixTestResult'),2).u16(a('gPcmLayerMixTestResult'))==0
 assert h.mem(a('gPcmLayerMixDemoReady'),2).u16(a('gPcmLayerMixDemoReady'))==1
 state_addr=a('gPcmLayerMixerState')
 def state(tag):
  m=h.mem(state_addr,0x114)
  active=[not bool(m.bytes(state_addr+0xb8,1)[0]),m.u32(state_addr+8)!=0,m.u32(state_addr+16)!=0,m.u32(state_addr+24)!=0]
  print(tag,active,flush=True);return active
 assert not any(state('startup'))
 print('startup shot',h.screenshot(),flush=True)
 h.tap('F9');h.tap('F5')
 assert all(state('four layers'))
 print('raster shot',h.screenshot(),flush=True)
 h.wait(2.2)
 assert state('loops after one-shots end')==[True,True,False,False]
 ring=state_addr+0x118
 pcm=h.mem(ring,2048).bytes(ring,2048)
 raw=(root/'VOICE.RAW').read_bytes();ref=bytes((b*2)&255 for b in raw)
 assert pcm[:256] in ref+ref
 assert h.mem(0xffff8921,1).bytes(0xffff8921,1)==b'\x81'
 assert h.mem(0xffff8240,2).u16(0xffff8240)==0
 print('DMA ring matches reference for two looping layers; palette restored',flush=True)
 h.tap('F1');assert state('base stopped')==[False,True,False,False]
 h.tap('F2');assert not any(state('second loop stopped'))
 h.tap('F3');h.wait(2.2);assert not any(state('one-shot completed'))
 h.tap('F5');h.tap('F6');assert not any(state('stop all'))
 h.tap('F9');h.control('hatari-event keydown 01');h.wait(.1);h.control('hatari-event keyup 01');h.wait(1)
 print('desktop shot',h.screenshot(),flush=True)
 (root/'analysis/hatari.log').write_text('\n'.join(h.lines))
 assert not any('ERROR' in l or 'Exception' in l or 'Address Error' in l or 'Bus Error' in l for l in h.lines)
print('PASS PCM Layer: self-test, four layers, two loops, one-shot end, stop, raster and ESC',flush=True)
