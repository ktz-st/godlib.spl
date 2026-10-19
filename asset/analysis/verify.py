#!/usr/bin/env python3
"""Exercise real linked assets and package lifetimes in disposable Hatari drives."""
from pathlib import Path
import os,sys,time,tempfile,shutil,json,hashlib
from PIL import Image
os.environ.setdefault('SDL_VIDEODRIVER','dummy');os.environ.setdefault('SDL_AUDIODRIVER','dummy')
sys.path.insert(0,str(Path.home()/'.agents/skills/hatari-debugging/scripts'))
from hatari_session import HatariSession,nm_symbols
root=Path(__file__).resolve().parents[1];out=root/'analysis'
hatari='/opt/homebrew/opt/hatari/Hatari.app/Contents/MacOS/hatari';tos=str(Path.home()/'Atari/tos/TOS v1.62 (1990)(Atari Corp)(STE)(De).img')
results=[]
with tempfile.TemporaryDirectory(prefix='godlib-asset-') as tmp:
 tmp=Path(tmp)
 for mode,exe,symfile in [('core',out/'ASTEST.PRG',out/'ASTEST.PRG'),('ui',root/'ASSETS.PRG',out/'ASDEBUG.PRG')]:
  if '--ui-only' in sys.argv and mode=='core':continue
  folder=tmp/mode;folder.mkdir();run=folder/exe.name;shutil.copy2(exe,run)
  for directory in ['UNLINK','DATA']:shutil.copytree(root/directory,folder/directory)
  sy=nm_symbols(str(symfile),nm='m68k-atari-mintelf-nm')
  with HatariSession(str(run),hatari=hatari,tos=tos,screenshot_dir=str(out/'shots'/mode),debug_except='bus,address,illegal',extra_args=['--confirm-quit','false','--memsize','1','--cpuclock','8','--monitor','rgb']) as h:
   h.wait(9);base=h.basepage()['text']
   def data(name,size):
    p=out/'dump.bin';p.unlink(missing_ok=True);h.debug(f'savebin {p} ${base+sy[name]:x} ${size:x}',settle=.05)
    for _ in range(100):
     if p.exists() and p.stat().st_size==size:return p.read_bytes()
     time.sleep(.01)
    raise AssertionError(h.lines[-20:])
   def val(name,size=2):return int.from_bytes(data(name,size),'big')
   def longs(name):b=data(name,16);return [int.from_bytes(b[i:i+4],'big')for i in range(0,16,4)]
   def key(scan):h.control(f'hatari-event keydown 0x{scan:02x}',settle=.20);h.control(f'hatari-event keyup 0x{scan:02x}',settle=.20)
   def settle_frames():
    if mode=='ui':
     first=val('gAssetFrames',4);deadline=time.time()+20
     while val('gAssetFrames',4)<first+3 and time.time()<deadline:h.wait(.05)
     assert val('gAssetFrames',4)>=first+3,'renderer did not complete three frames'
   def snap(name):
    settle_frames();im=Image.open(h.screenshot());im.save(out/(name+'.png'))
    if mode=='ui' and val('gAssetLoaded'):
     assert len(im.crop((96,138,736,338)).getcolors(65536))>8,'castle not visible'

   def wait_loaded(selected):
    deadline=time.time()+8
    while time.time()<deadline:
     if val('gAssetMode')==selected and val('gAssetLoaded')==1:
      settle_frames();return
     h.wait(.1)
    raise AssertionError(('load',selected,val('gAssetError'),h.lines[-15:]))
   def unloaded():
    assert val('gAssetLoaded')==0 and val('gAssetPointersCleared')==1
    assert val('gAssetRefCount')==4 and val('gAssetFreeNow',4)==val('gAssetFreeBase',4)
   try:
    deadline=time.time()+45
    ready='gAssetTestDone' if mode=='core' else 'gAssetReady'
    while not val(ready) and time.time()<deadline:h.wait(.15)
    if mode=='core':
     print('core',val('gAssetTestDone'),val('gAssetTestPass'),val('gAssetTestStage'),flush=True)
     assert val('gAssetTestDone')==1 and val('gAssetTestPass')==1,('stage',val('gAssetTestStage'),h.lines[-20:])
     snap('core');key(1);h.wait(.3);assert h.basepage()['text']!=base
     results.append('28 native checks: target GodPack byte-exact decompression, disk and RAM LNK access/sizes, every asset versus loose original, borrowed/owned data lifetime, free RAM recovery, missing members and multi-client callbacks/removal/refcounts')
    else:
     assert val('gAssetReady')==1;wait_loaded(2);assert val('gAssetInside')==1 and val('gAssetEqual')==1
     assert val('gAssetFiles')==3 and val('gAssetStored',4)<val('gAssetRawSize',4)
     snap('packed');reference=data('gAssetHash',12)
     for selected,scan in [(0,2),(1,3),(2,4)]:
      key(22);unloaded();snap('unloaded')
      key(scan);wait_loaded(selected)
      assert data('gAssetHash',12)==reference and val('gAssetEqual')==1 and val('gAssetError')==0
      assert val('gAssetRefCount')==5 and val('gAssetFiles')==3 and val('gAssetFlags')==1
      if selected:assert val('gAssetInside')==1
      snap(['loose','raw','packed'][selected])
     # Repeated reloads exercise delocation, pointer clearing, ownership and queues.
     for _ in range(3):key(19);wait_loaded(2)
     loads=longs('gAssetLoadCalls');unloads=longs('gAssetUnloadCalls')
     assert len(set(loads))==1 and all(a==b+1 for a,b in zip(loads,unloads)),(loads,unloads)
     key(22);unloaded();assert longs('gAssetLoadCalls')==longs('gAssetUnloadCalls')
     # Missing pack leaves all clients null; restoring it permits retry.
     packed=folder/'DATA/PACKED.LNK';parked=folder/'DATA/PACKED.BAK';packed.rename(parked)
     key(4);assert val('gAssetError')==1;unloaded();parked.rename(packed);key(19);wait_loaded(2)
     h.control('hatari-event keydown 0x01',settle=.6);h.control('hatari-event keyup 0x01');h.wait(.4)
     assert val('gAssetExited')==1 and val('gAssetFinalRefs',4)==0 and h.basepage()['text']!=base
     assert longs('gAssetLoadCalls')==longs('gAssetUnloadCalls')
     results.append('Three PackageManager modes with PI1/BFB/BSB rendering, auto relocation, equal asset hashes, duplicate font clients, unload/reload cycles, RAM recovery, missing-pack retry and clean exit to TOS')
    assert not any('cpu exception' in line.lower() for line in h.lines),h.lines[-15:]
   except BaseException:
    snap('failure-'+mode);(out/('failure-'+mode+'.log')).write_text('\n'.join(h.lines));raise
report={'result':'PASS','machine':'STE / 68000 / 8 MHz / 1 MiB / German TOS 1.62','release_sha256':hashlib.sha256((root/'ASSETS.PRG').read_bytes()).hexdigest(),'checks':results,'archives':json.loads((root/'assets/build.json').read_text()),'files':'copied to disposable GEMDOS folders; original assets untouched'}
(out/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
