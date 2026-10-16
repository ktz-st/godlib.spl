import os,sys,time,json,subprocess
from pathlib import Path
sys.path.insert(0,str(Path.home()/'.codex/skills/hatari-debugging/scripts'))
from hatari_session import HatariSession
root=Path(__file__).resolve().parents[1]
nm=subprocess.check_output(['m68k-atari-mintelf-nm','-n',str(root/'analysis/PCMBLDBG.TOS')],text=True)
syms={line.split()[2]:int(line.split()[0],16) for line in nm.splitlines() if len(line.split())==3}
with HatariSession(str(root/'PCMBLOCK.TOS'),screenshot_dir=str(root/'analysis/shots'),sound=False,tos=os.environ.get('HATARI_TOS'),debug_except='bus,address,illegal',extra_args=['--confirm-quit','false','--memsize','4','--monitor','rgb']) as h:
 h.wait(7)
 base=h.basepage(); print('basepage',base,flush=True)
 text=base['text']; a=lambda name:text+syms[name]
 def check_dma(rate):
  hw=h.mem(0xffff8921,1)
  vals=list(hw.data.values())
  print('DMA mode',vals[:2],flush=True)
  assert vals and vals[0]==(0x80|rate)
  ptr=h.mem(a('gPcmBlockMixerBuffer'),4).u32(a('gPcmBlockMixerBuffer'))
  pcm=h.mem(ptr,1024).bytes(ptr,1024)
  assert any(pcm)
  raw=(root/('VOICE25.RAW' if rate==2 else 'VOICE12.RAW')).read_bytes()
  expected={bytes((b*4)&255 for b in raw[i:i+512]) for i in range(0,len(raw),512)}
  assert pcm[:512] in expected and pcm[512:] in expected
  print('DMA ring matches 4-channel reference PCM',flush=True)
 def state(tag):
  m=h.mem(a('gPcmBlockMixDemoLoops'),8)
  chans=h.mem(a('gPcmBlockMixerChannels'),48)
  result={'tag':tag,'ready':m.u16(a('gPcmBlockMixDemoReady')),'rate':m.u16(a('gPcmBlockMixDemoRate')),'loops':m.u16(a('gPcmBlockMixDemoLoops')),'active':[chans.u32(a('gPcmBlockMixerChannels')+i*12)!=0 for i in range(4)]}
  print(json.dumps(result),flush=True); return result
 assert h.mem(a('gPcmBlockMixTestResult'),2).u16(a('gPcmBlockMixTestResult'))==0
 s=state('startup'); assert s['ready']==1 and s['rate']==2
 print('shot',h.screenshot(),flush=True)
 h.tap('F9'); h.tap('F6'); s=state('25k loops'); assert all(s['active'])
 h.wait(2.2); s=state('25k loops after sample length'); assert all(s['active']); check_dma(2)
 h.tap('F8'); s=state('12k switch'); assert s['rate']==1 and not any(s['active'])
 h.tap('F6'); s=state('12k loops'); assert all(s['active'])
 h.wait(2.2); s=state('12k loops after sample length'); assert all(s['active']); check_dma(1)
 print('raster shot',h.screenshot(),flush=True)
 assert h.mem(0xffff8240,2).u16(0xffff8240)==0
 h.tap('F9')
 h.tap('F7'); s=state('stop'); assert not any(s['active'])
 h.tap('F5'); h.wait(2.5); s=state('oneshots finished'); assert not any(s['active'])
 h.control('hatari-event keydown 01');h.wait(.1);h.control('hatari-event keyup 01'); h.wait(1)
 print('exit shot',h.screenshot(),flush=True)
 (root/'analysis/hatari.log').write_text('\n'.join(h.lines))
 assert not any('ERROR' in line or 'Exception' in line or 'Address Error' in line or 'Bus Error' in line for line in h.lines)
print('Hatari STE: ASM self-test, both rates, 4-channel loops, stop, one-shot end and ESC passed',flush=True)
