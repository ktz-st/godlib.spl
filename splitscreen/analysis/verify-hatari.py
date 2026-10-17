"""Check the displayed split, independent HUD and horizontal-blank counter writes."""
from pathlib import Path
import json, os, re, shutil, struct, subprocess, sys, tempfile
from PIL import Image
sys.path.insert(0,str(Path.home()/'.codex/skills/hatari-debugging/scripts'))
from hatari_session import HatariSession
root=Path(__file__).resolve().parents[1]
nm=subprocess.check_output(['m68k-atari-mintelf-nm',str(root/'analysis/SPLITDBG.PRG')],text=True)
syms={p[2]:int(p[0],16) for line in nm.splitlines() if len(p:=line.split())==3}
rom=os.environ.get('HATARI_TOS','/Users/kriss/Atari/tos/TOS v2.06 (1991)(Atari Corp)(Mega-STE)(UK).img')
data=(root/'TOWER.BIN').read_bytes();palette=struct.unpack_from('>16H',data)
colours=[tuple((((((v>>s)&7)<<1)|(((v>>s)>>3)&1))*17) for s in (8,4,0)) for v in palette]
def decode(raw,height):
 pixels=[]
 for y in range(height):
  for group in range(20):
   planes=struct.unpack_from('>4H',raw,y*160+group*8)
   pixels.extend(colours[sum(((planes[p]>>(15-x))&1)<<p for p in range(4))] for x in range(16))
 return pixels
terrain=decode(data[32:],400)
trace=root/'analysis/video.log'
with tempfile.TemporaryDirectory(prefix='split-test-') as td:
 program=Path(td)/'SPLIT.PRG';shutil.copy2(root/'SPLIT.PRG',program)
 with HatariSession(str(program),machine='ste',sound=False,screenshot_dir=str(root/'analysis/shots'),debug_except='bus,address,illegal',extra_args=['--confirm-quit','false','--memsize','4','--cpulevel','0','--cpuclock','8','--monitor','rgb','--tos',rom,'--trace','video_ste','--trace-file',str(trace)]) as h:
  h.wait(8);base=h.basepage()['text']
  def addr(name):return base+syms[name]
  def word(name):
   a=addr(name);return h.mem(a,2).u16(a)
  def setword(name,value):h.debug('w $%x $%02x $%02x'%(addr(name),value>>8,value&255))
  assert word('gSplitReady')==1
  old=word('gSplitY');h.wait(.3);assert word('gSplitY')!=old
  h.tap('2');assert word('gSplitSpeed')==4
  h.wait(1);h.tap('SPACE');assert word('gSplitAuto')==0
  a=addr('gSplitPanelCanvas');panel=h.mem(a,4).u32(a)
  raw=h.mem(panel,6400).bytes(panel,6400);hud=decode(raw,40)
  positions=(0,1,7,8,15,31,239,240)
  for y in positions:
   setword('gSplitY',y);h.wait(.15)
   shot=h.screenshot();im=Image.open(shot).convert('RGB')
   assert im.size==(832,588),im.size
   actual=list(im.crop((96,58,736,458)).resize((320,200),Image.Resampling.NEAREST).getdata())
   expected=terrain[y*320:(y+160)*320]+hud
   if actual!=expected:
    mismatch=next(i for i,(a,b) in enumerate(zip(actual,expected)) if a!=b)
    raise AssertionError((y,mismatch%320,mismatch//320,actual[mismatch],expected[mismatch],shot))
   print('PASS all displayed pixels, scroll Y=',y,flush=True)
  setword('gSplitY',0);h.tap('DOWN',hold=.2);assert 0<word('gSplitY')<240
  setword('gSplitY',240);h.tap('UP',hold=.2);assert 0<word('gSplitY')<240
  assert h.mem(panel,6400).bytes(panel,6400)==raw
  h.control('hatari-event keydown 01');h.wait(.3);h.control('hatari-event keyup 01');h.wait(1)
  assert word('gSplitExited')==1
  a=addr('gScreenClass');assert h.mem(a,4).u32(a)==0
  vector=h.mem(0x120,4).u32(0x120);assert not addr('Split_TimerB')<=vector<addr('Split_TimerBEnd')
  print('PASS controls, fixed HUD, timer removed and clean exit:',h.screenshot(),flush=True)
  assert not any('Address Error' in line or 'Bus Error' in line for line in h.lines)
  (root/'analysis/hatari.log').write_text('\n'.join(h.lines))
 writes=[]
 for line in trace.read_text().splitlines():
  m=re.search(r'write ste video (ff820[579]).*offset=(\w+).*line_cyc_w=(\d+).*nHBL=(\d+).*pc=(\w+)',line)
  if m and addr('Split_TimerB')<=int(m[5],16)<addr('Split_TimerBEnd'):
   assert int(m[2],16)==0 and int(m[4])==222 and 404<int(m[3])<512,line
   writes.append(m)
 assert len(writes)>=300 and len(writes)%3==0,len(writes)
 result=dict(machine='Hatari STE 68000 8 MHz PAL, TOS 2.06',pixel_checked_scroll_y=list(positions),terrain_rows=160,hud_rows=40,split_frames=len(writes)//3,counter_write_cycles=[min(int(m[3]) for m in writes),max(int(m[3]) for m in writes)],controls_and_exit='passed')
 (root/'analysis/results.json').write_text(json.dumps(result,indent=2)+'\n')
 print('PASS:',json.dumps(result),flush=True)
