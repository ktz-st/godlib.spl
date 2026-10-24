from common import *

report={'full_buffer_checks':0,'byte_mismatches':0,'cases':[]}
with HatariSession(str(DEBUG),hatari='/opt/homebrew/opt/hatari/Hatari.app/Contents/MacOS/hatari',tos=str(TOS),extra_args=['--confirm-quit','false','--memsize','1','--cpulevel','0','--cpuclock','8','--monitor','rgb','--fast-forward','true']) as h:
 p=Probe(h);p.put('gDwHold',1);p.put('gDwPaused',1);h.wait(.08)
 def check(page,mask,phase):
  actual=p.raw(pages[page],32000);ref=expected(back,mask,phase)
  errors=sum(a!=b for a,b in zip(actual,ref))
  assert not errors,(page,mask,phase,errors,next((i for i,(a,b) in enumerate(zip(actual,ref)) if a!=b),None))
  report['full_buffer_checks']+=1
 for mode,mask in enumerate(MASKS):
  p.put('gDwMode',mode);p.put('gDwMask',mask);p.put('gDwPhase',0);p.put('gDwReset',1);p.request();pages=p.pages();back=p.raw(pages[2],32000)
  check(0,mask,0);page=1
  for phase in range(1,257):
   p.put('gDwPhase',phase&255);p.request();check(page,mask,phase&255);page^=1
  # Both pages converge to a paused target, then remain byte-identical.
  for _ in range(4):p.request();check(page,mask,0);page^=1
  report['cases'].append({'mode':NAMES[mode],'mask':mask,'all_256_phases':True,'phase_wrap':True,'paused_both_pages':True})
  print('PASS',NAMES[mode],flush=True)
 # Arbitrary mode/phase jumps exercise direct recomposition, restoring inactive
 # planes, edge refills and +/- reversals without resetting either page.
 for i in range(60):
  mode=i%3;mask=MASKS[mode];phase=(i*97)&255
  p.put('gDwMode',mode);p.put('gDwMask',mask);p.put('gDwPhase',phase);p.request();check(page,mask,phase);page^=1
 p.put('gDwHold',0);h.wait(.15)
 for mode in range(3):
  h.tap(str(mode+1),hold=.05,after=.08);assert p.val('gDwMode')==mode and p.val('gDwMask')==MASKS[mode]
  phase=p.val('gDwPhase');pages=p.pages();back=p.raw(pages[2],32000)
  for page in (0,1):check(page,MASKS[mode],phase)
  p.preview(pages[0],f'preview-{NAMES[mode]}.png')
  assert p.raw(0xff8240,32)==PALETTE
 phase=p.val('gDwPhase');h.wait(.12);assert p.val('gDwPhase')==phase
 h.tap('N',hold=.04,after=.08);assert p.val('gDwPaused')==1 and p.val('gDwPhase')==(phase+1)&255
 h.tap('SPACE',hold=.04,after=.1);assert p.val('gDwPaused')==0
 first=p.val('gDwFrames',4);h.wait(.2);assert p.val('gDwFrames',4)>first
 h.control('hatari-event keydown 01');h.wait(.12);h.control('hatari-event keyup 01');h.wait(.2);assert p.val('gDwExited')==1
 report.update({'mode_phase_jumps':60,'controls_palette_exit':True,'machine':'STE 68000 8 MHz PAL RGB, 1 MiB, German TOS 1.62','release_sha256':hashlib.sha256((APP/'DCKWAVE.PRG').read_bytes()).hexdigest()})
 (APP/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print(report['full_buffer_checks'],'full native buffers passed',flush=True)
