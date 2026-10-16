"""ST/STE full-image reference, unchanged VRAM, palette-write timing and cleanup."""
from pathlib import Path
import json, os, re, shutil, struct, subprocess, sys, tempfile
from PIL import Image
sys.path.insert(0,str(Path.home()/'.codex/skills/hatari-debugging/scripts'))
from hatari_session import HatariSession
root=Path(__file__).resolve().parents[1]
nm=subprocess.check_output(['m68k-atari-mintelf-nm',str(root/'analysis/PALDBG.PRG')],text=True)
syms={p[2]:int(p[0],16) for line in nm.splitlines() if len(p:=line.split())==3}
rom=os.environ.get('HATARI_TOS','/Users/kriss/Atari/tos/TOS v2.06 (1991)(Atari Corp)(Mega-STE)(UK).img')
data=(root/'COAST.PI1').read_bytes();palette=struct.unpack_from('>16H',data,2)
grey=[]
for c in palette:
 r,g,b=[(c>>s)&7 for s in (8,4,0)];y=(77*r+150*g+29*b+128)//256
 grey.append(y*0x111)
def colours(pal):return [tuple(((c>>s)&7)*34 for s in (8,4,0)) for c in pal]
indices=[]
for row in range(200):
 for group in range(20):
  planes=struct.unpack_from('>4H',data,34+row*160+group*8)
  indices.extend(sum(((planes[p]>>(15-x))&1)<<p for p in range(4)) for x in range(16))
colour=colours(palette);gray=colours(grey)
expected_colour=bytes(v for i in indices for v in colour[i])
expected_split=bytes(v for pos,i in enumerate(indices) for v in (colour if pos<32000 else gray)[i])
results=[]
rom162=os.environ.get('HATARI_TOS162','/Users/kriss/Atari/tos/TOS v1.62 (1990)(Atari Corp)(STE)(GB)[STE TOS, Rev 2].img')
for machine,version,testrom in (('st','2.06',rom),('ste','2.06',rom),('ste','1.62',rom162)):
 label=machine+'-'+version
 trace=root/('analysis/'+label+'-video.log')
 with tempfile.TemporaryDirectory(prefix='pal-test-') as td:
  program=Path(td)/'PALFX.PRG';shutil.copy2(root/'PALFX.PRG',program)
  with HatariSession(str(program),machine=machine,sound=False,screenshot_dir=str(root/'analysis/shots'/label),debug_except='bus,address,illegal',extra_args=['--confirm-quit','false','--memsize','4','--cpulevel','0','--cpuclock','8','--monitor','rgb','--tos',testrom,'--trace','video_color','--trace-file',str(trace)]) as h:
   h.wait(8);base=h.basepage()['text']
   def addr(name):return base+syms[name]
   def word(name):
    a=addr(name);return h.mem(a,2).u16(a)
   assert word('gPalSplitReady')==1
   a=addr('gPalSplitGrey');assert h.mem(a,32).bytes(a,32)==struct.pack('>16H',*grey)
   shots=[]
   def check(expected):
    shot=h.screenshot();im=Image.open(shot).convert('RGB');assert im.size==(832,588),im.size
    actual=im.crop((96,58,736,458)).resize((320,200),Image.Resampling.NEAREST).tobytes()
    if actual!=expected:
     i=next(i for i,(a,b) in enumerate(zip(actual,expected)) if a!=b)
     raise AssertionError((machine,(i//3)%320,(i//3)//320,actual[i],expected[i],shot))
    shots.append(shot)
   for _ in range(3):check(expected_split);h.wait(.2)
   h.tap('SPACE');assert word('gPalSplitEnabled')==0;check(expected_colour)
   h.tap('SPACE');assert word('gPalSplitEnabled')==1;check(expected_split)
   # Changing hardware palette must leave every pixel word in both pages intact.
   for name in ('gScreenLogicGraphic','gScreenPhysicGraphic','gScreenBackGraphic'):
    a=addr(name);page=h.mem(a,4).u32(a)
    assert h.mem(page,32000).bytes(page,32000)==data[34:32034]
   h.control('hatari-event keydown 01');h.wait(.3);h.control('hatari-event keyup 01');h.wait(5)
   assert word('gPalSplitExited')==1
   a=addr('gScreenClass');assert h.mem(a,4).u32(a)==0
   vector=h.mem(0x120,4).u32(0x120);assert not addr('PalSplit_TimerB')<=vector<addr('PalSplit_TimerBEnd')
   assert not any('Address Error' in l or 'Bus Error' in l for l in h.lines)
   print(label,'PASS pixels, toggle, unchanged VRAM and exit',flush=True)
   (root/('analysis/'+label+'-hatari.log')).write_text('\n'.join(h.lines))
  writes=[]
  for line in trace.read_text().splitlines():
   m=re.search(r'write col addr=(\w+) col=(\w+).*line_cyc_w=(\d+).*nHBL=(\d+).*pc=(\w+)',line)
   if m and addr('PalSplit_TimerB')<=int(m[5],16)<addr('PalSplit_TimerBEnd'):
    assert int(m[4])==162 and 376<=int(m[3])<512,line
    writes.append((int(m[1],16),int(m[2],16)&0x777,int(m[3])))
  assert len(writes)>=1600 and len(writes)%16==0,len(writes)
  for i in range(0,len(writes),16):
   assert [w[0] for w in writes[i:i+16]]==list(range(0xff8240,0xff8260,2))
   assert [w[1] for w in writes[i:i+16]]==grey
  result=dict(machine=machine,tos=version,filename='PALFX.PRG',cpu='68000 8 MHz',video='PAL 320x200',split_line=100,pixel_checked_frames=5,palette_split_frames=len(writes)//16,palette_write_cycles=[min(w[2] for w in writes),max(w[2] for w in writes)],unchanged_vram=True,controls_and_exit='passed')
  results.append(result);print(json.dumps(result),flush=True)
(root/'analysis/results.json').write_text(json.dumps(results,indent=2)+'\n')
