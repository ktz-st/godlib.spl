from common import *
report={'full_buffer_checks':0,'byte_mismatches':0,'coverage':[]}
with HatariSession(str(DEBUG),hatari='/opt/homebrew/opt/hatari/Hatari.app/Contents/MacOS/hatari',tos=str(TOS),machine='ste',extra_args=['--confirm-quit','false','--memsize','1','--cpulevel','0','--cpuclock','8','--monitor','rgb','--fast-forward','true'])as h:
 p=Probe(h);p.put('gDbHold',1);p.put('gDbPaused',1);h.wait(.05);pages=p.pages();back=p.raw(pages[2],32000);p.put('gDbReset',1)
 def check(mode,mask,phase,both=False):
  p.put('gDbMode',mode);p.put('gDbMask',mask);p.put('gDbPhase',phase)
  for _ in range(2 if both else 1):
   p.request();dest=p.val('gDbDest',4)-24*160;actual=p.raw(dest,32000);want=expected(back,mode,mask,phase)
   if actual!=want:
    off=next(i for i in range(32000)if actual[i]!=want[i]);raise AssertionError((mode,mask,phase,off,actual[off:off+16].hex(),want[off:off+16].hex()))
   report['full_buffer_checks']+=1
 # First reset restores both pages and resets phase to zero.
 check(0,15,0,True)
 # Every phase, one complete cycle each, mixing plane masks between families.
 for mode,mask in [(0,15),(1,2),(2,15),(3,5)]:
  for phase in range(160):check(mode,mask,phase)
  check(mode,mask,0,True);report['coverage'].append({'mode':NAMES[mode],'mask':mask,'all_160_phases':True})
  print('PASS phases',NAMES[mode],report['full_buffer_checks'],flush=True)
 # Strips have ten distinct states; the intermediate phases must leave a
 # settled page unchanged and consume no block-copy commands.
 for phase in range(0,160,16):
  check(4,15,phase,True);check(4,15,phase+1,True);assert p.val('gDbCount')==0
 report['coverage'].append({'mode':'strips','all_10_states_and_idle':True})
 # All 16 masks in each of the three kernel widths, including the zero mask.
 for mode in (0,1,4):
  for mask in range(16):check(mode,mask,37,True)
 print('PASS masks',report['full_buffer_checks'],flush=True)
 # Mixed mode/mask jumps without reset test restoration of dropped planes
 # and full-stage <-> small moving rectangle changes on both page histories.
 for n in range(48):check(n%5,(n*7)&15,(n*53)%160)
 for ptr in pages[:2]:assert p.raw(ptr,24*160)==back[:24*160] and p.raw(ptr+184*160,16*160)==back[184*160:]
 assert p.raw(p.addr('Db_Picture'),25600)==PICTURE
 assert p.raw(pages[2],32000)==back
 # Let real input select the modes and exercise pause, step and mask changes.
 p.put('gDbMask',15);p.put('gDbHold',0);h.wait(.1)
 for mode in range(5):
  p.key(mode+2);assert p.val('gDbMode')==mode
  pages=p.pages();back=p.raw(pages[2],32000);phase=p.val('gDbPhase')
  for page in(0,1):assert p.raw(pages[page],32000)==expected(back,mode,15,phase);report['full_buffer_checks']+=1
  p.preview(pages[0],f'preview-{NAMES[mode]}.png')
 for mask in (2,5,15):p.key(50);assert p.val('gDbMask')==mask
 phase=p.val('gDbPhase');p.key(49);assert p.val('gDbPaused')==1 and p.val('gDbPhase')==(phase+1)%160
 p.key(19);assert p.val('gDbRaster')==1
 p.key(57);assert p.val('gDbPaused')==0
 h.wait(.15);p.exit()
 report.update({'all_16_masks_and_3_widths':True,'mode_mask_jumps':48,'source_and_clean_back_unchanged':True,'outside_stage_unchanged':True,'controls_palette_exit':True,'machine':'STE 68000 8 MHz PAL RGB, 1 MiB, German TOS 1.62','release_sha256':hashlib.sha256((APP/'DCKBLOCK.PRG').read_bytes()).hexdigest()})
 (APP/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print(report,flush=True)
