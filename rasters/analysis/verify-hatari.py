"""Check the raster list, all displayed pixels and PAL timing on ST/STE."""
from pathlib import Path
import json,os,re,shutil,struct,subprocess,sys,tempfile
from PIL import Image
# Keep scripted keyboard scenarios isolated from physical keyboard input.
os.environ.setdefault("SDL_VIDEODRIVER","dummy")
sys.path.insert(0,str(Path.home()/'.codex/skills/hatari-debugging/scripts'))
from hatari_session import HatariSession
root=Path(__file__).resolve().parents[1]
nm=subprocess.check_output(['m68k-atari-mintelf-nm',str(root/'analysis/RDBG.PRG')],text=True)
syms={p[2]:int(p[0],16) for line in nm.splitlines() if len(p:=line.split())==3}
rom=os.environ.get('HATARI_TOS','/Users/kriss/Atari/tos/TOS v2.06 (1991)(Atari Corp)(Mega-STE)(UK).img')
rom162=os.environ.get('HATARI_TOS162','/Users/kriss/Atari/tos/TOS v1.62 (1990)(Atari Corp)(STE)(GB)[STE TOS, Rev 2].img')
levels=[0,0,1,1,2,3,4,5,7,5,4,3,2,1,1,0]
lut=[]
for band in range(4):
 for level in levels:
  lut.append([(level<<8)|((level//2)<<4),(level<<4)|level,(level<<8)|level,((level//2)<<8)|(level<<4)][band])
def rgb(c):return tuple(((c>>s)&7)*34 for s in (8,4,0))
results=[]
for machine,version,tos in [('st','2.06',rom),('ste','2.06',rom),('ste','1.62',rom162)]:
 label=machine+'-'+version;trace=root/('analysis/'+label+'-video.log')
 with tempfile.TemporaryDirectory(prefix='raster-test-') as td:
  prog=Path(td)/'RASTR.PRG';shutil.copy2(root/'RASTR.PRG',prog)
  with HatariSession(str(prog),machine=machine,sound=False,screenshot_dir=str(root/'analysis/shots'/label),debug_except='bus,address,illegal',extra_args=['--confirm-quit','false','--memsize','4','--cpulevel','0','--cpuclock','8','--monitor','rgb','--tos',tos,'--trace','video_color','--trace-file',str(trace)]) as h:
   h.wait(8);base=h.basepage()['text']
   def addr(name):return base+syms[name]
   def word(name):
    a=addr(name);return h.mem(a,2).u16(a)
   def setword(name,v):h.debug('w $%x $%02x $%02x'%(addr(name),v>>8,v&255))
   assert word('gRasterReady')==1
   a=addr('gRasterPhase');old=word('gRasterPhase');h.wait(.15);assert word('gRasterPhase')!=old
   h.tap('2');assert word('gRasterSpeed')==2
   h.tap('SPACE');assert word('gRasterAnimate')==0
   a=addr('gRasterLut');assert h.mem(a,128).bytes(a,128)==struct.pack('>64H',*lut)
   a=addr('gScreenBackGraphic');page=h.mem(a,4).u32(a);raw=h.mem(page,32000).bytes(page,32000)
   a=addr('gRasterPalette');pal=list(struct.unpack('>16H',h.mem(a,32).bytes(a,32)))
   indices=[]
   for y in range(200):
    for group in range(20):
     planes=struct.unpack_from('>4H',raw,y*160+group*8)
     indices.extend(sum(((planes[p]>>(15-x))&1)<<p for p in range(4)) for x in range(16))
   assert 0 in indices and 15 in indices
   def check(phase,enabled):
    expected=bytes(channel for pos,index in enumerate(indices) for channel in rgb(pal[index] if index else lut[(pos//1280+phase)&63] if enabled else 0x012))
    shot=h.screenshot();im=Image.open(shot).convert('RGB');assert im.size==(832,588)
    actual=im.crop((96,58,736,458)).resize((320,200),Image.Resampling.NEAREST).tobytes()
    if actual!=expected:
     i=next(i for i,(a,b) in enumerate(zip(actual,expected)) if a!=b)
     raise AssertionError((label,phase,enabled,(i//3)%320,(i//3)//320,actual[i],expected[i],shot))
   phases=(0,1,17,32,63)
   for phase in phases:
    setword('gRasterPhase',phase);h.wait(.15);assert word('gRasterFramePhase')==phase
    check(phase,True);print(label,'PASS all pixels phase',phase,flush=True)
   h.tap('R');assert word('gRasterEnabled')==0;assert word('gRasterAnimate')==0;check(63,False)
   h.tap('R');assert word('gRasterEnabled')==1;assert word('gRasterAnimate')==0;check(63,True)
   h.control('hatari-event keydown 01');h.wait(.3);h.control('hatari-event keyup 01');h.wait(5)
   assert word('gRasterExited')==1
   a=addr('gScreenClass');assert h.mem(a,4).u32(a)==0
   vector=h.mem(0x120,4).u32(0x120);assert not addr('Raster_TimerB')<=vector<addr('Raster_TimerBEnd')
   assert not any('Bus Error' in l or 'Address Error' in l for l in h.lines)
   (root/('analysis/'+label+'-hatari.log')).write_text('\n'.join(h.lines))
  writes=[]
  for line in trace.read_text().splitlines():
   m=re.search(r'write col addr=(\w+) col=(\w+).*line_cyc_w=(\d+).*nHBL=(\d+).*pc=(\w+)',line)
   if m and addr('Raster_TimerB')<=int(m[5],16)<addr('Raster_TimerBEnd'):
    assert int(m[1],16)==0xff8240 and 376<=int(m[3])<512,line
    writes.append((int(m[4]),int(m[3])))
  assert len(writes)>=4900 and len(writes)%49==0,len(writes)
  for i in range(0,len(writes),49):assert [w[0] for w in writes[i:i+49]]==list(range(66,259,4)),writes[i:i+49]
  result=dict(machine=machine,tos=version,cpu='68000 8 MHz PAL',bands=50,interrupts_per_active_frame=49,pixel_phases=list(phases),complete_raster_frames=len(writes)//49,write_cycles=[min(w[1] for w in writes),max(w[1] for w in writes)],controls_and_exit='passed')
  results.append(result);print(json.dumps(result),flush=True)
(root/'analysis/results.json').write_text(json.dumps(results,indent=2)+'\n')
