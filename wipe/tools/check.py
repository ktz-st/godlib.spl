from common import *

report={'full_buffer_checks':0,'byte_mismatches':0,'guard_checks':0,'cases':[]}
with HatariSession(str(staged()),hatari='/opt/homebrew/opt/hatari/Hatari.app/Contents/MacOS/hatari',tos=str(TOS),extra_args=['--confirm-quit','false','--memsize','1','--cpulevel','0','--cpuclock','8','--monitor','rgb','--fast-forward','true']) as h:
 p=Probe(h);assert p.val('gWipeBlitter')==1;p.put('gWipeBenchHold',1);h.wait(.08)
 assert list(struct.unpack('>39H',p.data('gWipeFrameCounts',78)))==COUNTS
 dest=p.addr('gWipeBenchMemory');guard=struct.pack('>8H',*([0xa55a]*8))
 # BLiTTER first; CPU and per-step mixed backends must reproduce an independent
 # planar reference for every mask, not just agree with each other at the end.
 for mode in ['blitter','cpu','mixed']:
  for closing in (0,1):
   p.put('gWipeBenchClosing',closing)
   for effect in range(39):
    p.put('gWipeBenchEffect',effect);p.put('gWipeBenchReset',1)
    p.put('gWipeBenchBackend',int(mode=='blitter'))
    for frame in range(COUNTS[effect]):
     backend=(frame&1) if mode=='mixed' else int(mode=='blitter')
     if mode=='mixed':p.put('gWipeBenchBackend',backend)
     h.debug(f'w ${p.addr("gWipeBenchRequest"):x} $0 $1',settle=.002)
     for _ in range(100):
      raw=p.raw(dest,32040,settle=.002)
      actual_backend,finished,abi,counter=struct.unpack_from('>4H',raw,32032)
      if counter==frame+1:break
      h.wait(.005)
     assert counter==frame+1,(mode,effect,frame,counter)
     assert actual_backend==backend and abi==0
     assert raw[:16]==guard and raw[32016:32032]==guard,(mode,closing,effect,frame,'guard')
     actual=raw[16:32016];ref=reference(effect,frame,closing);assert actual==ref,(mode,closing,effect+1,frame,sum(a!=b for a,b in zip(actual,ref)))
     assert finished==int(frame==COUNTS[effect]-1),(effect,frame,'completion')
     report['full_buffer_checks']+=1;report['guard_checks']+=1
    assert p.val('gWipeBenchAbiFailed')==0,(mode,closing,effect,'ABI')
    report['cases'].append({'backend':mode,'closing':closing,'effect':effect+1,'frames':COUNTS[effect],'abi_preserved':True})
   print('PASS all 39',mode,('out' if closing else 'in'),flush=True)
 assert p.raw(p.val('gWipeBenchSource',4),32000)==PICTURES[0],'source was modified'
 for invalid in [39,0x8000,0xffff]:
  for closing in (0,1):
   p.put('gWipeBenchEffect',invalid);p.put('gWipeBenchClosing',closing);p.put('gWipeBenchReset',1);p.request()
   assert p.val('gWipeBenchFinished')==1
   assert p.raw(dest+16,32000)==(PICTURES[0] if closing else bytes(32000))
 # Restore the actual slideshow after using the module's global state in tests.
 p.put('gWipeBenchBackend',1);p.request(4);p.put('gWipeHoldOnBlack',1);p.put('gWipeBenchHold',0)
 h.tap('SPACE',hold=.04,after=.08);p.waitval('gWipeAtBlack',1)
 assert p.raw(p.pages()[2],32000)==bytes(32000)
 assert art_equal(p.raw(p.val('gWipePresented',4),32000),bytes(32000))
 assert p.raw(0xff8240,32)==PALETTES[0]
 p.put('gWipeHoldOnBlack',0)
 for image in [1,2,0]:
  for _ in range(100):
   if p.val('gSlideIndex')==image and p.val('gWipeStage')==1:break
   h.wait(.025)
  assert p.val('gSlideIndex')==image and p.val('gWipeStage')==1
  h.tap('P',hold=.025,after=.04) if not p.val('gAutoPause') else None
  assert p.raw(p.pages()[2],32000)==PICTURES[image]
  assert p.raw(0xff8240,32)==PALETTES[image]
  assert art_equal(p.raw(p.val('gWipePresented',4),32000),PICTURES[image])
  if image==1:
   h.tap('B',hold=.025,after=.04);assert p.val('gWipeBlitter')==0
   h.tap('B',hold=.025,after=.04);assert p.val('gWipeBlitter')==1
   h.tap('R',hold=.025,after=.04);assert p.val('gWipeRaster')==1
  if image!=0:h.tap('SPACE',hold=.025,after=.05)
 old_vector=p.val('gVblOldHandler',4);h.control('hatari-event keydown 01');h.wait(.12);h.control('hatari-event keyup 01');h.wait(.4)
 assert p.val('gWipeExited')==1 and int.from_bytes(p.raw(0x70,4),'big')==old_vector
 report.update({'all_39_effects_both_directions':True,'mid_transition_backend_changes':True,'source_unchanged':True,'unsigned_invalid_indices_ignored':True,'slideshow_three_images_and_palette_seam':True,'keyboard_backend_stripe_pause_next':True,'clean_exit_vbl_restored':True,'machine':'STE 68000 8 MHz PAL RGB, 1 MiB, German TOS 1.62','release_sha256':hashlib.sha256((APP/'WIPE.PRG').read_bytes()).hexdigest(),'godlib_archive_sha256':hashlib.sha256((APP.parents[1]/'godlib/libgod.a').read_bytes()).hexdigest()})
 (APP/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print(report['full_buffer_checks'],'complete guarded buffers passed',flush=True)
