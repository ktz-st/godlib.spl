from common import *

release=(APP/'WIPE.PRG').read_bytes();assert DEBUG.read_bytes()==release
symbols=Path(os.environ.get('WIPE_SYMBOLS','/tmp/WIPEREL.PRG')).read_bytes();t,d=struct.unpack_from('>2I',release,2)
assert symbols[28+0xa0:28+t+d]==release[28+0xa0:28+t+d]
machine=os.environ.get('WIPE_MACHINE','ste');hardware=int(machine=='ste');runs=[]
with HatariSession(str(staged()),machine=machine,hatari='/opt/homebrew/opt/hatari/Hatari.app/Contents/MacOS/hatari',tos=str(TOS),extra_args=['--confirm-quit','false','--memsize','1','--cpulevel','0','--cpuclock','8','--blitter','true' if hardware else 'false','--monitor','rgb','--fast-forward','true']) as h:
 p=Probe(h);assert p.val('gWipeBlitter')==hardware;p.put('gAutoPause',1);p.waitval('gWipeStage',1)
 def finished(image):
  for _ in range(150):
   if p.val('gSlideIndex')==image and p.val('gWipeStage')==1:break
   h.wait(.02)
  assert p.val('gSlideIndex')==image and p.val('gWipeStage')==1
  assert p.raw(p.pages()[2],32000)==PICTURES[image]
  for ptr in p.pages()[:2]:assert art_equal(p.raw(ptr,32000),PICTURES[image])
  actual=struct.unpack('>16H',p.raw(0xff8240,32));expected=struct.unpack('>16H',PALETTES[image]);mask=0xfff if hardware else 0x777
  assert [w&mask for w in actual]==[w&mask for w in expected]
 for desired in (0,1):
  if p.val('gWipeBlitter')!=desired:h.tap('B',hold=.025,after=.04)
  expected=desired if hardware else 0;assert p.val('gWipeBlitter')==expected
  image=(p.val('gSlideIndex')+1)%3;h.tap('SPACE',hold=.025,after=.04);finished(image)
  runs.append({'requested_backend':desired,'actual_backend':expected,'final_image':image})
 # Slow to real time for an observable key switch during a running transition.
 h.control('hatari-option --fast-forward false');h.tap('SPACE',hold=.025,after=.025)
 assert p.val('gWipeStage')!=1
 before=p.val('gWipeBlitter');ticks=p.val('gWipeTicks');image=(p.val('gSlideIndex')+1)%3
 h.tap('B',hold=.025,after=.025);assert p.val('gWipeBlitter')==(1-before if hardware else 0)
 assert p.val('gWipeTicks')>=ticks
 h.control('hatari-option --fast-forward true');finished(image)
 h.tap('P',hold=.025,after=.025);assert p.val('gAutoPause')==0
 h.tap('P',hold=.025,after=.025);assert p.val('gAutoPause')==1
 h.tap('R',hold=.025,after=.025);assert p.val('gWipeRaster')==1
 old_vector=p.val('gVblOldHandler',4);h.control('hatari-event keydown 01');h.wait(.12);h.control('hatari-event keyup 01');h.wait(.4)
 assert p.val('gWipeExited')==1 and int.from_bytes(p.raw(0x70,4),'big')==old_vector
 result={'actual_shipped_prg_tested':True,'code_data_matches_external_symbols':True,'machine':machine,'ram_mib':1,'hardware_blitter':bool(hardware),'runs':runs,'native_images_and_palettes':True,'both_display_pages':True,'keyboard_backend_change_mid_transition':True,'auto_pause_and_stripe':True,'clean_exit_vbl_restored':True,'release_sha256':hashlib.sha256(release).hexdigest()}
 (APP/('release-smoke-st.json' if machine=='st' else 'release-smoke.json')).write_text(json.dumps(result,indent=2)+'\n');print(result)
