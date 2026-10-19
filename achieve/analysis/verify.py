#!/usr/bin/env python3
"""Run both core regression and interactive sample in disposable GEMDOS folders."""
from pathlib import Path
import hashlib,json,os,shutil,struct,sys,tempfile,time
from PIL import Image
os.environ.setdefault('SDL_VIDEODRIVER','dummy');os.environ.setdefault('SDL_AUDIODRIVER','dummy')
sys.path.insert(0,str(Path.home()/'.agents/skills/hatari-debugging/scripts'))
from hatari_session import HatariSession,nm_symbols
root=Path(__file__).resolve().parents[1];out=root/'analysis'
hatari='/opt/homebrew/opt/hatari/Hatari.app/Contents/MacOS/hatari';tos=str(Path.home()/'Atari/tos/TOS v1.62 (1990)(Atari Corp)(STE)(De).img')
results=[]
with tempfile.TemporaryDirectory(prefix='godlib-achieve-')as tmp:
 tmp=Path(tmp)
 for mode,exe,symbols in [('core',out/'ACHTEST.PRG',out/'ACHTEST.PRG'),('ui',root/'ACHIEVE.PRG',out/'ACHDBG.PRG')]:
  
  if '--ui-only' in sys.argv and mode=='core':continue
  folder=tmp/mode;folder.mkdir();run=folder/exe.name;shutil.copy2(exe,run);sy=nm_symbols(str(symbols),nm='m68k-atari-mintelf-nm')
  with HatariSession(str(run),hatari=hatari,tos=tos,screenshot_dir=str(out/'shots'/mode),debug_except='bus,address,illegal',extra_args=['--confirm-quit','false','--memsize','1','--cpuclock','8','--monitor','rgb'])as h:
   h.wait(9);base=h.basepage()['text']
   def dump(name,size):
    p=out/'dump.bin';p.unlink(missing_ok=True);h.debug(f'savebin {p} ${base+sy[name]:x} ${size:x}',settle=.05)
    for _ in range(100):
     if p.exists()and p.stat().st_size==size:return p.read_bytes()
     time.sleep(.01)
    raise AssertionError(h.lines[-20:])
   def word(n):return int.from_bytes(dump(n,2),'big')
   def long(n):return int.from_bytes(dump(n,4),'big')
   def player():return dump('gAchPlayer',16).split(b'\0')[0].decode('ascii')
   def key(scan):h.control('hatari-event keydown '+f'{scan:02d}',settle=.10);h.control('hatari-event keyup '+f'{scan:02d}',settle=.15)
   def snap(name):Image.open(h.screenshot()).save(out/(name+'.png'))
   try:
    if mode=='core':
     print('core',word('gAchTestDone'),word('gAchTestPass'),word('gAchTestStage'),flush=True)
     assert word('gAchTestDone')==1 and word('gAchTestPass')==1,('stage',word('gAchTestStage'),h.lines[-20:])
     results.append('29 native core checks: profiles, score order/ties, stats, partial-byte tasks, specs, disk round trips across buffers and failed-load preservation')
     snap('core');key(1)
    else:
     assert word('gAchReady')==1 and player()=='ATARI' and word('gAchUsers')==1
     assert long('gAchGames')==0 and long('gAchTop')==2000;snap('scores')
     key(28);assert long('gAchGames')==1 and word('gAchUnlocked')==1 and word('gAchNew')==1
     key(77);key(28);assert long('gAchGames')==2 and long('gAchBest')==1000 and word('gAchUnlocked')==2
     key(28);assert long('gAchGames')==3 and word('gAchUnlocked')==3 and word('gAchPoints')==85
     key(15);assert word('gAchTab')==1;snap('awards')
     key(30);assert word('gAchNew')==0
     # Name editing, delete and a prefix name distinct from ATARI.
     key(49);assert word('gAchEditing')==1
     for sc in [30,20,30,19,23,14]:key(sc) # ATARI then backspace -> ATAR
     key(28);assert player()=='ATAR' and word('gAchUsers')==2 and long('gAchGames')==0
     key(28);assert long('gAchGames')==1 and word('gAchUnlocked')==2
     key(31);assert word('gAchSaveOK')==1
     saved=folder/'ACHDEMO.DAT';assert saved.exists() and saved.stat().st_size>100
     disk_hash=hashlib.sha256(saved.read_bytes()).hexdigest();old=long('gAchArenaAddress')
     key(28);assert long('gAchGames')==2
     key(38);assert word('gAchLoadOK')==1 and long('gAchArenaAddress')!=old
     assert player()=='ATARI' and long('gAchGames')==3 and word('gAchUnlocked')==3
     key(49)
     for sc in [30,20,30,19]:key(sc)
     key(28);assert player()=='ATAR' and long('gAchGames')==1 and word('gAchUsers')==2
     snap('loaded');assert hashlib.sha256(saved.read_bytes()).hexdigest()==disk_hash
     key(1);h.wait(.5);assert h.basepage()['text']!=base and word('gAchExited')==1
     results.append('Real IKBD UI: two distinct names, text editing, three unlocks/85 points, acknowledgement, Save/Load into another arena, retained players/stats and exit to TOS')
    assert not any('cpu exception'in line.lower()for line in h.lines),h.lines[-20:]
   except BaseException:
    snap('failure-'+mode);(out/('failure-'+mode+'.log')).write_text('\n'.join(h.lines));raise
report={'result':'PASS','machine':'STE / 68000 / 8 MHz / 1 MiB / German TOS 1.62','release_sha256':hashlib.sha256((root/'ACHIEVE.PRG').read_bytes()).hexdigest(),'checks':results,'save_location':'temporary disposable GEMDOS folders; existing user saves untouched'}
(out/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
