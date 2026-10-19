#!/usr/bin/env python3
"""Native codec regression plus real IKBD and emulated joystick integration."""
from pathlib import Path
import os,sys,time,tempfile,shutil,json,hashlib
from PIL import Image
os.environ.setdefault('SDL_VIDEODRIVER','dummy');os.environ.setdefault('SDL_AUDIODRIVER','dummy')
sys.path.insert(0,str(Path.home()/'.agents/skills/hatari-debugging/scripts'))
from hatari_session import HatariSession,nm_symbols
root=Path(__file__).resolve().parents[1];out=root/'analysis'
hatari='/opt/homebrew/opt/hatari/Hatari.app/Contents/MacOS/hatari'
tos=str(Path.home()/'Atari/tos/TOS v1.62 (1990)(Atari Corp)(STE)(De).img')
results=[];stats={}
with tempfile.TemporaryDirectory(prefix='godlib-input-') as temp:
 temp=Path(temp);cfg=temp/'joy.cfg'
 cfg.write_text('[Joystick1]\nnJoystickMode = 2\nbEnableAutoFire = FALSE\nkUp = w\nkDown = s\nkLeft = a\nkRight = d\nkFire = j\n')
 for mode,exe,symfile in [('core',out/'INTEST.PRG',out/'INTEST.PRG'),('ui',root/'INPUT.PRG',out/'INDEBUG.PRG')]:
  if '--ui-only' in sys.argv and mode=='core':continue
  folder=temp/mode;folder.mkdir();run=folder/exe.name;shutil.copy2(exe,run)
  sy=nm_symbols(str(symfile),nm='m68k-atari-mintelf-nm')
  with HatariSession(str(run),hatari=hatari,tos=tos,screenshot_dir=str(out/'shots'/mode),debug_except='bus,address,illegal',extra_args=['--configfile',str(cfg),'--joy0','none','--joy1','keys','--confirm-quit','false','--memsize','1','--cpuclock','8','--monitor','rgb']) as h:
   h.wait(9);base=h.basepage()['text']
   def value(name,size=2):
    p=out/'dump.bin';p.unlink(missing_ok=True);h.debug(f'savebin {p} ${base+sy[name]:x} ${size:x}',settle=.05)
    for _ in range(100):
     if p.exists() and p.stat().st_size==size:return int.from_bytes(p.read_bytes(),'big')
     time.sleep(.01)
    raise AssertionError(h.lines[-10:])
   def event(command):
    before=value('gInFrames',4) if mode=='ui' else 0
    h.control(command,settle=.08)
    if mode=='ui':
     deadline=time.time()+5
     while value('gInFrames',4)<before+2 and time.time()<deadline:h.wait(.03)
   def down(sc):event(f'hatari-event keydown {sc:02d}')
   def up(sc):event(f'hatari-event keyup {sc:02d}')
   def key(sc):down(sc);up(sc)
   def joy(char,held):event('hatari-event '+('keydown ' if held else 'keyup ')+char)
   def snap(name):Image.open(h.screenshot()).save(out/(name+'.png'))
   try:
    if mode=='core':
     print('core',value('gInputTestDone'),value('gInputTestPass'),value('gInputTestStage'),flush=True)
     assert value('gInputTestDone')==1 and value('gInputTestPass')==1,('stage',value('gInputTestStage'),h.lines[-15:])
     snap('core');key(1);h.wait(.4);assert h.basepage()['text']!=base
     results.append('36 native checks: combined held/hit/release and rapid re-press, byte-exact delta round trip, unchanged/all-byte frames, exact capacity, overflow, neutral EOF, replay rewind, disk load validation, failure preservation, callback/DTA cleanup and re-init')
    else:
     assert value('gInReady')==1 and value('gInTaskInit')==1
     start=value('gInX');down(77);h.wait(.12);assert value('gInX')>start and value('gInKeys')==1
     joy('d',True);assert value('gInJoy')&8
     up(77);state=(value('gInKeys'),value('gInJoy'),value('gInHeld'));assert state[0]==0 and state[1]&8 and state[2]&2,state
     joy('d',False);assert not value('gInHeld')&2
     # Fire handover from keyboard to joystick must be one action, no extra HIT.
     fire=value('gInFires');down(57);joy('j',True);up(57)
     assert value('gInHeld')&16 and value('gInFires')==fire+1
     joy('j',False);key(57);assert value('gInFires')==fire+2;snap('live')
     key(19);assert value('gInMode')==1
     down(75);h.wait(.18);up(75);down(80);h.wait(.12);up(80);key(57)
     joy('d',True);h.wait(.15);joy('d',False);joy('j',True);joy('j',False)
     key(19);assert value('gInMode')==0
     frames=value('gInRecordFrames',4);size=value('gInBytes',4);end=(value('gInX'),value('gInY'),value('gInFires'))
     print("recorded",frames,size,end,flush=True)
     assert frames>5 and 36<=size<frames*36 and end[2]==2,(frames,size,end)
     snap('recorded');key(31);assert value('gInSaveOK')==1
     saved=folder/'INPUTS.KIP';assert saved.stat().st_size==size;disk=hashlib.sha256(saved.read_bytes()).hexdigest()
     key(25);assert value('gInMode')==2
     # Unrecorded live movement while replaying must not change replay results.
     down(72);h.wait(.25);up(72)
     deadline=time.time()+15
     while not value('gInChecks') and time.time()<deadline:h.wait(.1)
     assert value('gInChecks')==1 and value('gInMatch')==1 and value('gInMode')==0
     assert (value('gInX'),value('gInY'),value('gInFires'))==end
     snap('matched');key(38);assert value('gInLoadOK')==1 and value('gInMode')==2
     deadline=time.time()+15
     while value('gInMode')==2 and time.time()<deadline:h.wait(.1)
     assert value('gInMode')==0 and (value('gInX'),value('gInY'),value('gInFires'))==end
     assert hashlib.sha256(saved.read_bytes()).hexdigest()==disk
     key(25);assert value('gInMode')==2;key(25);assert value('gInMode')==0
     h.control('hatari-event keydown 01',settle=.5);h.control('hatari-event keyup 01');h.wait(.4);assert value('gInExited')==1 and value('gInTaskDeInit')==1 and value('gInCallsAfterExit',4)==0 and h.basepage()['text']!=base
     stats={'frames':frames,'bytes':size,'endpoint':end,'file_sha256':disk}
     results.append('Real keyboard plus Hatari joystick 1 packets: direction/fire handover, recording, replay digest and endpoint match despite live keys, KIP save/load replay, abort, nonzero task index 7, exactly one task deinit and clean TOS exit')
    assert not any('cpu exception' in line.lower() for line in h.lines),h.lines[-15:]
   except BaseException:
    snap('failure-'+mode);(out/('failure-'+mode+'.log')).write_text('\n'.join(h.lines));raise
report={'result':'PASS','machine':'STE / 68000 / 8 MHz / 1 MiB / German TOS 1.62','release_sha256':hashlib.sha256((root/'INPUT.PRG').read_bytes()).hexdigest(),'checks':results,'recording':stats,'files':'temporary disposable GEMDOS directories; no existing recordings overwritten'}
(out/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
