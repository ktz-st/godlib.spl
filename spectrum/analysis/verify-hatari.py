"""Independent SPU decoding, full displayed pixels and cycle-exact write traces."""
from pathlib import Path
import json,os,re,struct,subprocess,sys,time
from PIL import Image
os.environ.setdefault('SDL_VIDEODRIVER','dummy');sys.path.insert(0,str(Path.home()/'.codex/skills/hatari-debugging/scripts'))
from hatari_session import HatariSession
r=Path(__file__).resolve().parents[1]
sym={p[2]:int(p[0],16) for l in subprocess.check_output(['m68k-atari-mintelf-nm',str(r/'analysis/PDBG.PRG')],text=True).splitlines() if len(p:=l.split())==3}
chart='--chart' in sys.argv
if chart:sys.argv.remove('--chart')
b=(r/('assets/CHART.SPU' if chart else 'assets/PICTURE.SPU')).read_bytes();pal=struct.unpack('>9552H',b[32000:])
indices=[]
for y in range(200):
 for group in range(20):
  words=struct.unpack_from('>4H',bytes(160)+b[160:],y*160+group*8)
  indices.extend(sum(((v>>(15-x))&1)<<p for p,v in enumerate(words)) for x in range(16))
def reference(ste,enabled):
 out=bytearray()
 for pos,c in enumerate(indices):
  y,x=divmod(pos,320)
  if y==0:v=0
  elif not enabled:v=pal[c]
  else:
   threshold=10*c+(-5 if c&1 else 1)
   idx=c+(32 if x>=threshold+160 else 16 if x>=threshold else 0)
   v=pal[(y-1)*48+idx]
  if not ste:v&=0x777
  out.extend((((v>>s)&7)*2+((v>>(s+3))&1))*17 for s in (8,4,0))
 return bytes(out)
configs=[('st','2.06','TOS v2.06 (1991)(Atari Corp)(Mega-STE)(UK).img'),('ste','2.06','TOS v2.06 (1991)(Atari Corp)(Mega-STE)(UK).img'),('ste','1.62','TOS v1.62 (1990)(Atari Corp)(STE)(GB)[STE TOS, Rev 2].img')]
if len(sys.argv)>1:configs=[c for c in configs if c[0]+'-'+c[1]==sys.argv[1]]
results=[]
for machine,version,rom in configs:
 label=machine+'-'+version;trace=r/('analysis/'+('chart-' if chart else '')+label+'.trace')
 with HatariSession(str(r/('SPEC4K.PRG' if chart else 'SPEC.PRG')),machine=machine,sound=False,screenshot_dir=str(r/'analysis/shots'/label/str(int(time.time()))),debug_except='bus,address,illegal',extra_args=['--tos',str(Path.home()/'Atari/tos'/rom),'--confirm-quit','false','--memsize','1','--cpuclock','8','--cpulevel','0','--monitor','rgb','--borders','false','--statusbar','false','--zoom','1','--trace-file',str(trace)]) as h:
  h.wait(8);base=h.basepage()['text']
  def addr(n):return base+sym[n]
  def word(n):
   a=addr(n);return h.mem(a,2).u16(a)
  assert word('gSpectrumReady')==1 and word('gSpectrumSTE')==(machine=='ste')
  checks=[]
  if chart:
   rgb=reference(machine=='ste',True)
   colours={tuple(rgb[i:i+3]) for i in range(0,len(rgb),3)}
   assert len(colours)==(4096 if machine=='ste' else 512),len(colours)
  def check(ste,enabled):
   h.wait(.1);shot=h.screenshot();im=Image.open(shot).convert('RGB');assert im.size in [(640,400),(320,200)],im.size
   actual=im.resize((320,200),Image.Resampling.NEAREST).tobytes();expected=reference(ste,enabled)
   if actual!=expected:
    diffs=[i for i,(a,b) in enumerate(zip(actual,expected)) if a!=b]
    i=diffs[0];raise AssertionError((label,ste,enabled,len(diffs),(i//3)%320,(i//3)//320,actual[i:i+3],expected[i:i+3],shot))
   checks.append({'ste_palette':ste,'rasters':enabled,'all_64000_pixels_match':True,'screenshot':shot})
   print(label,'PASS', '4096' if ste else '512','rasters',enabled,flush=True)
  check(machine=='ste',True)
  h.tap('1');assert word('gSpectrumFrameMode')==0;check(False,True)
  h.tap('2');assert word('gSpectrumFrameMode')==(machine=='ste');check(machine=='ste',True)
  h.tap('SPACE');assert word('gSpectrumActive')==0;check(machine=='ste',False)
  h.tap('SPACE');assert word('gSpectrumActive')==1;check(machine=='ste',True)
  h.debug('trace video_color',settle=.1);h.wait(.15);h.debug('trace none',settle=.1)
  h.control('hatari-event keydown 01');h.wait(.3);h.control('hatari-event keyup 01');h.wait(5)
  assert word('gSpectrumExited')==1
  v=h.mem(0x134,4).u32(0x134);assert v!=addr('Spectrum_TimerA')
  v=h.mem(0x68,4).u32(0x68);assert v!=addr('Spectrum_Hbl')
  assert not any(any(e in l for e in ('Bus Error','Address Error','Illegal instruction')) for l in h.lines)
  frames=[];current=[];pattern=re.compile(r'write col addr=(\w+) col=(\w+).*line_cyc_w=(\d+).*nHBL=(\d+).*pc=(\w+)')
  for line in trace.open():
   m=pattern.search(line)
   if not m:continue
   reg,col,cyc,row,pc=int(m[1],16),int(m[2],16),int(m[3]),int(m[4]),int(m[5],16)
   if not addr('Spectrum_Code')<=pc<addr('Spectrum_CodeEnd'):continue
   if pc==addr('Spectrum_Code') and reg==0xff8240:
    if len(current)==9552:frames.append(current)
    current=[]
   current.append((reg,col,cyc,row))
  if len(current)==9552:frames.append(current)
  assert len(frames)>=3,len(frames)
  for frame in frames:
   for i,(reg,col,cyc,row) in enumerate(frame):
    line,word=divmod(i,48);bank,k=divmod(word,16)
    phase=404+[0,192,352][bank]+(k//2)*20+(k%2)*4
    expected_row=63+line+phase//512;expected_cycle=phase%512
    assert (reg,cyc,row)==(0xff8240+(k*2),expected_cycle,expected_row),(label,i,(reg,cyc,row),(expected_cycle,expected_row))
    expected=pal[i] if machine=='ste' else pal[i]&0x777
    assert (col& (0xfff if machine=='ste' else 0x777))==expected
  result={'machine':machine,'tos':version,'ram_mb':1,'asset':'chart' if chart else 'picture','distinct_displayed_colours':len(colours) if chart else None,'cpu':'68000 8 MHz, PAL','checks':checks,'complete_timing_frames':len(frames),'palette_words_per_frame':9552,'first_palette_write':'line 63 cycle 404','scanline_period_cycles':512,'timer_a_hbl_restored_and_exit':True}
  results.append(result);print(label,'PASS',len(frames),'complete frames with cycle-exact palette writes',flush=True)
(r/('analysis/results'+('-chart' if chart else '')+('-'+sys.argv[1] if len(sys.argv)>1 else '')+'.json')).write_text(json.dumps(results,indent=2)+'\n')
