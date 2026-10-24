from pathlib import Path
import sys,os,time,json,struct,tempfile,shutil
os.environ['SDL_VIDEODRIVER']='dummy';os.environ['SDL_AUDIODRIVER']='dummy'
sys.path.insert(0,str(Path.home()/'.agents/skills/hatari-debugging/scripts'))
from hatari_session import HatariSession,nm_symbols
from hrdb_profile import Rdb,profile_lines
r=Path(tempfile.mkdtemp(prefix='sndh-dck-psg-live-'));app=Path(__file__).resolve().parents[1];shutil.copyfile(app/'build/SNDBG.PRG',r/'SNDHDBG.PRG');shutil.copyfile(app/'popcorn.snd',r/'popcorn.snd');sy=nm_symbols(str(r/'SNDHDBG.PRG'),nm='m68k-atari-mintelf-nm');ranges=['PsgVis_Snapshot','PsgVis_Update','PsgExtra_Update','PsgDck_Update']
with HatariSession(str(r/'SNDHDBG.PRG'),hatari='/opt/homebrew/opt/hatari-hrdb/Applications/hatari-hrdb/Hatari-HRDB.app/Contents/MacOS/Hatari',tos=str(Path.home()/'Atari/tos/TOS v1.62 (1990)(Atari Corp)(STE)(De).img'),sound=True,screenshot_dir=str(r),extra_args=['--confirm-quit','false','--memsize','1','--cpulevel','0','--cpuclock','8','--monitor','rgb','--fast-forward','true'])as h:
 h.wait(3);base=h.basepage()['text'];a=lambda n:base+sy[n]
 def raw(addr,size):
  p=r/'live.bin';p.unlink(missing_ok=True);h.debug(f'savebin {p} ${addr:x} ${size:x}',settle=.06)
  for _ in range(100):
   if p.exists()and p.stat().st_size==size:return p.read_bytes()
   time.sleep(.01)
  raise RuntimeError(h.lines[-20:])
 def val(n,size=2):return int.from_bytes(raw(a(n),size),'big')
 def waitmode(mode):
  for _ in range(30):
   if val('gSndVisMode')==mode:return
   h.wait(.1)
  raise RuntimeError(('mode',mode,val('gSndVisMode')))
 assert val('gSndVisReady')==1
 results=[]
 for mode in range(1,11):
  h.tap('O',hold=.05,after=.12);waitmode(mode)
  if mode<7:continue
  h.wait(.2);assert struct.unpack('>2H',raw(a('gSndVisPageView'),4))==(mode+1,mode+1)
  pages=struct.unpack('>4I',raw(a('gScreenClass')+4,16));back=raw(pages[2],32000)
  for ptr in pages[:2]:
   pixels=raw(ptr,32000)
   assert pixels[:40*160]==back[:40*160],('header',mode)
   assert pixels[176*160:]==back[176*160:],('footer',mode)
  # Decode the completed native page; debugger breaks can interrupt Hatari's scanout.
  from PIL import Image
  native=raw(pages[0],32000);pal=[0,0x700,0x070,0x770,0x007,0x707,0x077,0x777]+[0]*7+[0x777]
  colours=[tuple(((c>>shift)&7)*255//7 for shift in (8,4,0))for c in pal]
  im=Image.new('RGB',(320,200));out=[]
  for y in range(200):
   for group in range(20):
    words=struct.unpack_from('>4H',native,y*160+group*8)
    out.extend(colours[sum(((words[p]>>(15-bit))&1)<<p for p in range(4))]for bit in range(16))
  im.putdata(out);im.save(app/f'dck-psg-{mode-7}.png')
  rdb=Rdb(port=int(os.environ.get('SNDH_HRDB_PORT','56001')))
  play=val('gSndVisPlay',4)-8;size=(app/'popcorn.snd').stat().st_size
  f0=val('gSndVisFrames',4);miss0=val('gSndVisMissedVbl',4)
  rdb.cmd('break',wait=.15);rdb.cmd('profile 1',wait=.05);rdb.cmd('run',wait=.05);h.wait(1.2);rdb.cmd('break',wait=.25)
  msg=rdb.take('!profile')
  for _ in range(10):
   if msg:break
   rdb.pump(.2);msg=rdb.take('!profile')
  rows=profile_lines(msg);assert rows
  frames=sum(n for pc,n,c in rows if pc==a('SndVis_FrameDone'));assert frames>30
  calls=sum(n for pc,n,c in rows if pc==a('PsgDck_Draw'+str(mode-7)));assert abs(calls-frames)<=1,(calls,frames)
  cycles={name:sum(c for pc,n,c in rows if a(name)<=pc<a(name+'End'))for name in ranges}
  cycles['draw']=sum(c for pc,n,c in rows if a('PsgDck_Draw0')<=pc<a('PsgDck_DrawEnd'))
  cycles['music']=sum(c for pc,n,c in rows if play<=pc<play+size)
  result={'mode':mode,'frames':frames,'draw_calls':calls,'cycles':cycles,'cycles_per_frame':{k:v/frames for k,v in cycles.items()},'pal_frame_percent':{k:v/frames/1600 for k,v in cycles.items()}}
  result['new_mode_percent']=(cycles['PsgDck_Update']+cycles['draw'])/frames/1600
  result['visualization_total_percent']=(sum(cycles[n]for n in ranges)+cycles['draw'])/frames/1600
  rdb.cmd('profile 0',wait=.05);rdb.cmd('run',wait=.05);rdb.s.close()
  result['normal_frames']=val('gSndVisFrames',4)-f0;result['missed_vbls']=val('gSndVisMissedVbl',4)-miss0
  h.tap('V',hold=.05,after=.15);assert val('gSndVisEnabled')==0
  assert struct.unpack('>2H',raw(a('gSndVisPageView'),4))==(0,0)
  pages=struct.unpack('>4I',raw(a('gScreenClass')+4,16));back=raw(pages[2],32000)
  assert raw(pages[0],32000)==back and raw(pages[1],32000)==back
  h.tap('V',hold=.05,after=.15);assert val('gSndVisEnabled')==1
  results.append(result);print(result,flush=True)
 h.tap('O',hold=.05,after=.15);waitmode(0)
 h.control('hatari-event keydown 01');h.wait(.15);h.control('hatari-event keyup 01');h.wait(.2);assert val('gSndVisExited')==1
 report={'machine':'STE 68000 8 MHz PAL, 1 MiB, German TOS 1.62','tune':'popcorn.snd','eleven_mode_cycle':True,'hide_show_both_pages_clean':True,'exit':True,'profiles':results}
 (r/'live-results.json').write_text(json.dumps(report,indent=2)+'\n');(app/'dck-psg-results.json').write_text(json.dumps(report,indent=2)+'\n')
