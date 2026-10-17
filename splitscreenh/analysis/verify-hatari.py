"""Check the displayed split, independent HUD and horizontal-blank counter writes."""
from pathlib import Path
import json, os, re, shutil, struct, subprocess, sys, tempfile
from PIL import Image
os.environ.setdefault("SDL_VIDEODRIVER","dummy")
sys.path.insert(0,str(Path.home()/'.codex/skills/hatari-debugging/scripts'))
from hatari_session import HatariSession
from check_trace import check_trace
root=Path(__file__).resolve().parents[1]
nm=subprocess.check_output(['m68k-atari-mintelf-nm',str(root/'analysis/SPLITHDB.PRG')],text=True)
syms={p[2]:int(p[0],16) for line in nm.splitlines() if len(p:=line.split())==3}
version='1.62' if '--tos162' in sys.argv else '2.06'
rom=os.environ.get('HATARI_TOS','/Users/kriss/Atari/tos/TOS v2.06 (1991)(Atari Corp)(Mega-STE)(UK).img')
if version=='1.62':
 rom=os.environ.get('HATARI_TOS162','/Users/kriss/Atari/tos/TOS v1.62 (1990)(Atari Corp)(STE)(GB)[STE TOS, Rev 2].img')
tag='-tos162' if version=='1.62' else ''
data=(root/'PANORAMA.BIN').read_bytes();palette=struct.unpack_from('>16H',data)
colours=[tuple((((((v>>s)&7)<<1)|(((v>>s)>>3)&1))*17) for s in (8,4,0)) for v in palette]
def decode(raw,width,height,pal=palette):
 colours=[tuple((((((v>>s)&7)<<1)|(((v>>s)>>3)&1))*17) for s in (8,4,0)) for v in pal]
 pixels=[]
 for y in range(height):
  for group in range(width//16):
   planes=struct.unpack_from('>4H',raw,y*(width//2)+group*8)
   pixels.extend(colours[sum(((planes[p]>>(15-x))&1)<<p for p in range(4))] for x in range(16))
 return pixels
terrain=decode(data[32:],640,200)
trace=root/('analysis/video'+tag+'.log')
with tempfile.TemporaryDirectory(prefix='split-test-') as td:
 program=Path(td)/'SPLITH.PRG';shutil.copy2(root/'SPLITH.PRG',program)
 with HatariSession(str(program),machine='ste',sound=False,screenshot_dir=str(root/('analysis/shots'+tag)),debug_except='bus,address,illegal',extra_args=['--confirm-quit','false','--memsize','4','--cpulevel','0','--cpuclock','8','--monitor','rgb','--tos',rom,'--trace','video_ste,video_color','--trace-file',str(trace)]) as h:
  h.wait(8);base=h.basepage()['text']
  def addr(name):return base+syms[name]
  def word(name):
   a=addr(name);return h.mem(a,2).u16(a)
  def setword(name,value):h.debug('w $%x $%02x $%02x'%(addr(name),value>>8,value&255))
  assert word('gHSplitReady')==1
  old=word('gHSplitX');h.wait(.3);assert word('gHSplitX')!=old
  h.tap('2');assert word('gHSplitSpeed')==4
  h.wait(1);h.tap('SPACE');assert word('gHSplitAuto')==0
  a=addr('gHSplitPanelCanvas');panel=h.mem(a,4).u32(a)
  raw=h.mem(panel,2560).bytes(panel,2560)
  a=addr('gHSplitHudPalette');hudpal=struct.unpack('>16H',h.mem(a,32).bytes(a,32))
  assert hudpal[0]!=palette[0] and hudpal[15]!=palette[15]
  hud=decode(raw,320,16,hudpal)
  assert len(set(hud))==16, 'HUD swatches must exercise all 16 palette entries'
  positions=tuple(range(16))+(16,17,31,32,319,320)
  for y in positions:
   setword('gHSplitX',y);h.wait(.15)
   shot=h.screenshot();im=Image.open(shot).convert('RGB')
   assert im.size==(832,588),im.size
   actual_bytes=im.crop((96,58,736,458)).resize((320,200),Image.Resampling.NEAREST).tobytes()
   actual=[tuple(actual_bytes[i:i+3]) for i in range(0,len(actual_bytes),3)]
   expected=hud+[pixel for row in range(184) for pixel in terrain[row*640+y:row*640+y+320]]
   if actual!=expected:
    mismatch=next(i for i,(a,b) in enumerate(zip(actual,expected)) if a!=b)
    raise AssertionError((y,mismatch%320,mismatch//320,actual[mismatch],expected[mismatch],shot))
   print('PASS all displayed pixels, scroll X=',y,flush=True)
  setword('gHSplitX',0);h.tap('RIGHT',hold=.2);assert 0<word('gHSplitX')<320
  setword('gHSplitX',320);h.tap('LEFT',hold=.2);assert 0<word('gHSplitX')<320
  assert h.mem(panel,2560).bytes(panel,2560)==raw
  h.control('hatari-event keydown 01');h.wait(.3);h.control('hatari-event keyup 01');h.wait(5)
  assert word('gHSplitExited')==1
  a=addr('gScreenClass');assert h.mem(a,4).u32(a)==0
  vector=h.mem(0x120,4).u32(0x120);assert not addr('HSplit_TimerB')<=vector<addr('HSplit_TimerBEnd')
  print('PASS controls, fixed HUD, timer removed and clean exit:',h.screenshot(),flush=True)
  assert not any('Address Error' in line or 'Bus Error' in line for line in h.lines)
  (root/'analysis/hatari.log').write_text('\n'.join(h.lines))
 timing=check_trace(trace,addr('HSplit_TimerB'),addr('HSplit_TimerBEnd'),palette)
 result=dict(machine='Hatari STE 68000 8 MHz PAL, TOS '+version,pixel_checked_scroll_x=list(positions),terrain_rows=184,hud_rows=16,independent_palettes=True,**timing,controls_and_exit='passed')
 (root/('analysis/results'+tag+'.json')).write_text(json.dumps(result,indent=2)+'\n')
 print('PASS:',json.dumps(result),flush=True)
