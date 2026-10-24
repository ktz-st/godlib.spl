from pathlib import Path
import sys,os,time,json,struct,tempfile,shutil
os.environ['SDL_VIDEODRIVER']='dummy';os.environ['SDL_AUDIODRIVER']='dummy'
sys.path.insert(0,str(Path.home()/'.agents/skills/hatari-debugging/scripts'))
from hatari_session import HatariSession,nm_symbols
from hrdb_profile import Rdb,profile_lines
r=Path(tempfile.mkdtemp(prefix='sndh-histogram-live-'));app=Path(__file__).resolve().parents[1];shutil.copyfile(app/'build/SNDBG.PRG',r/'SNDHDBG.PRG');shutil.copyfile(app/'popcorn.snd',r/'popcorn.snd');sy=nm_symbols(str(r/'SNDHDBG.PRG'),nm='m68k-atari-mintelf-nm');ranges=['PsgVis_Snapshot','PsgVis_Update','PsgExtra_Update','PsgHistogram_Update','PsgHistogram_Draw']
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
 assert val('gSndVisReady')==1,h.lines[-30:]
 for mode in range(1,7):
  h.tap('O',hold=.05,after=.08);waitmode(mode)
 h.wait(.2);assert list(struct.unpack('>2H',raw(a('gSndVisPageView'),4)))==[7,7]
 h.screenshot();(app/'histogram-preview.png').write_bytes((r/'grab0001.png').read_bytes())
 # Independently inspect bar words and other planes on both live display pages.
 # At a debugger break, counter state is stable; previous per-page heights
 # describe the actual completed image on each page, even between updates.
 rdb=Rdb(port=int(os.environ.get('SNDH_HRDB_PORT','56001')))
 rdb.cmd('break',wait=.15)
 # Use remote memory reads only after resuming: the control debugger is not
 # used while hrdb holds a break. Full pixel checks are covered by fixtures.
 rdb.cmd('run',wait=.08)
 play=val('gSndVisPlay',4)-8;size=(app/'popcorn.snd').stat().st_size
 f0=val('gSndVisFrames',4);miss0=val('gSndVisMissedVbl',4)
 rdb.cmd('break',wait=.15);rdb.cmd('profile 1',wait=.05);rdb.cmd('run',wait=.05);h.wait(1.5);rdb.cmd('break',wait=.25)
 msg=rdb.take('!profile')
 for _ in range(10):
  if msg:break
  rdb.pump(.2);msg=rdb.take('!profile')
 rows=profile_lines(msg);assert rows
 frames=sum(n for pc,n,c in rows if pc==a('SndVis_FrameDone'));assert frames>30,frames
 counts={name:sum(n for pc,n,c in rows if pc==a(name))for name in ranges}
 assert abs(counts['PsgHistogram_Draw']-frames)<=1,counts
 cycles={name:sum(c for pc,n,c in rows if a(name)<=pc<a(name+'End'))for name in ranges};cycles['music']=sum(c for pc,n,c in rows if play<=pc<play+size)
 result={'frames':frames,'calls':counts,'cycles':cycles,'cycles_per_frame':{k:v/frames for k,v in cycles.items()},'pal_frame_percent':{k:v/frames/1600 for k,v in cycles.items()}}
 result['histogram_only_percent']=(cycles['PsgHistogram_Update']+cycles['PsgHistogram_Draw'])/frames/1600
 result['visualization_total_percent']=sum(cycles[name]for name in ranges)/frames/1600
 rdb.cmd('profile 0',wait=.05);rdb.cmd('run',wait=.05);rdb.s.close()
 result['normal_frames_after_profile']=val('gSndVisFrames',4)-f0;result['missed_vbls_in_window']=val('gSndVisMissedVbl',4)-miss0
 print(result,flush=True)
 h.tap('V',hold=.05,after=.15);assert val('gSndVisEnabled')==0
 for _ in range(15):
  views=struct.unpack('>2H',raw(a('gSndVisPageView'),4))
  if views==(0,0):break
  h.wait(.1)
 assert views==(0,0),views
 pages=struct.unpack('>4I',raw(a('gScreenClass')+4,16));back=raw(pages[2],32000)
 assert raw(pages[0],32000)==back and raw(pages[1],32000)==back
 h.tap('V',hold=.05,after=.15);assert val('gSndVisEnabled')==1
 for mode in (7,8,9,10,0):h.tap('O',hold=.05,after=.15);waitmode(mode)
 for mode in range(1,7):h.tap('O',hold=.05,after=.08);waitmode(mode)
 assert val('gSndVisMode')==6
 h.control('hatari-event keydown 01');h.wait(.15);h.control('hatari-event keyup 01');h.wait(.2);assert val('gSndVisExited')==1
 result['eleven_mode_cycle']=True;result['hide_both_pages_clean']=True;result['show_and_exit']=True
 (r/'live-results.json').write_text(json.dumps(result,indent=2)+'\n');(r/'live.log').write_text('\n'.join(h.lines))
