from pathlib import Path
import os,sys,time,struct,json,shutil,hashlib,tempfile
os.environ['SDL_VIDEODRIVER']='dummy';os.environ['SDL_AUDIODRIVER']='dummy'
sys.path.insert(0,str(Path.home()/'.agents/skills/hatari-debugging/scripts'))
from hatari_session import HatariSession,nm_symbols
from hrdb_profile import Rdb,profile_lines
r=Path(tempfile.mkdtemp(prefix='dck-mod-live-'));basepath=Path(__file__).resolve().parents[2];results=[]
variants=[('Lance25','LMDBG','lancemod','Lance','LOSTPARO.MOD'),('Leonard25','LEODBG','leonard','Leonard','LOSTPARO.MOD'),('Leonard12','LEO12DBG','leonard','Leonard','LOSTPARO.MOD'),('Wizzcat','WIZDBG','wizzcat','Wizzcat','QUICKIE.MOD')]
for name,dbg,folder,prefix,tune in variants:
 d=r/name;d.mkdir(exist_ok=True);shutil.copyfile(Path('/tmp')/(dbg+'.PRG'),d/'PLAYER.PRG');shutil.copyfile(basepath/folder/tune,d/tune);sy=nm_symbols(str(d/'PLAYER.PRG'),nm='m68k-atari-mintelf-nm');p='g'+prefix+'Vis'
 with HatariSession(str(d/'PLAYER.PRG'),hatari='/opt/homebrew/opt/hatari-hrdb/Applications/hatari-hrdb/Hatari-HRDB.app/Contents/MacOS/Hatari',tos=str(Path.home()/'Atari/tos/TOS v1.62 (1990)(Atari Corp)(STE)(De).img'),sound=True,screenshot_dir=str(d),extra_args=['--confirm-quit','false','--memsize','4','--cpulevel','0','--cpuclock','8','--monitor','rgb','--fast-forward','true'])as h:
  h.wait(3);base=h.basepage()['text'];a=lambda n:base+sy[n]
  def raw(addr,size):
   f=d/'state.bin';f.unlink(missing_ok=True);h.debug(f'savebin {f} ${addr:x} ${size:x}',settle=.05)
   for _ in range(100):
    if f.exists()and f.stat().st_size==size:return f.read_bytes()
    time.sleep(.005)
   raise RuntimeError(h.lines[-25:])
  def val(n,size=2):return int.from_bytes(raw(a(n),size),'big')
  def mode(expected):
   h.tap('O',hold=.045,after=.08)
   for _ in range(50):
    if val(p+'Mode')==expected:return
    h.wait(.1)
   raise RuntimeError((name,'mode',expected,val(p+'Mode')))
  for _ in range(60):
   if val(p+'Ready')==1:break
   h.wait(.1)
  assert val(p+'Ready')==1,(name,h.lines[-30:])
  for m in range(1,5):mode(m)
  rdb=Rdb(port=int(os.environ.get('DCK_MOD_HRDB_PORT','56001')))
  for m in range(5,10):
   mode(m);h.wait(.15)
   assert struct.unpack('>2H',raw(a(p+'PageView'),4))==(m+1,m+1)
   # hide and show checks both display buffers for each new style.
   h.tap('V',hold=.045,after=.15);assert val(p+'Enabled')==0
   pages=struct.unpack('>4I',raw(a('gScreenClass')+4,16));back=raw(pages[2],32000)
   assert raw(pages[0],32000)==back and raw(pages[1],32000)==back,(name,m,'hide')
   h.tap('V',hold=.045,after=.15);assert val(p+'Enabled')==1
   h.screenshot()
   f0=val(p+'Frames',4);miss0=val(p+'MissedVbl',4)
   rdb.cmd('break',wait=.15);rdb.cmd('profile 1',wait=.04);rdb.cmd('run',wait=.04);h.wait(.8);rdb.cmd('break',wait=.2)
   msg=rdb.take('!profile')
   for _ in range(10):
    if msg:break
    rdb.pump(.2);msg=rdb.take('!profile')
   rows=profile_lines(msg);assert rows
   frames=sum(n for pc,n,c in rows if pc==a(prefix+'Vis_FrameDone'));calls=sum(n for pc,n,c in rows if pc==a('DckModVis_Draw'+str(m-5)))
   assert frames>30 and abs(calls-frames)<=1,(name,m,frames,calls)
   cycles=sum(c for pc,n,c in rows if a('DckModVis_Draw0')<=pc<a('DckModVis_DrawEnd'))
   rdb.cmd('profile 0',wait=.04);rdb.cmd('run',wait=.04)
   item={'player':name,'mode':m,'style':m-5,'tune':tune,'frames':frames,'calls':calls,'cycles_per_frame':cycles/frames,'ms_8mhz':cycles/frames/8000,'pal_frame_percent':cycles/frames/1600,'native_frames_delta':val(p+'Frames',4)-f0,'missed_vbl_delta':val(p+'MissedVbl',4)-miss0,'both_pages_hidden_clean':True,'debug_sha256':hashlib.sha256((d/'PLAYER.PRG').read_bytes()).hexdigest()};results.append(item);print(item,flush=True);(r/'profiles.json').write_text(json.dumps(results,indent=2)+'\n')
  rdb.s.close();mode(0);assert val(p+'Mode')==0
  h.control('hatari-event keydown 01');h.wait(.15);h.control('hatari-event keyup 01');h.wait(.2);assert val(p+'Exited')==1,(name,'exit')
  if prefix=='Leonard':assert val('gLeonardVisAudioDetached')==1
  (d/'hatari.log').write_text('\n'.join(h.lines))
 print(name,'ten-mode cycle/hide/exit PASS',flush=True)
