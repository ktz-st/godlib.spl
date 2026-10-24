from common import *
report={'full_buffer_checks':0,'byte_mismatches':0,'cases':[]}
with HatariSession(str(DEBUG),hatari='/opt/homebrew/opt/hatari/Hatari.app/Contents/MacOS/hatari',tos=str(TOS),extra_args=['--confirm-quit','false','--memsize','1','--cpulevel','0','--cpuclock','8','--monitor','rgb','--fast-forward','true'])as h:
 p=Probe(h);p.put('gLwHold',1);h.wait(.1)
 for image in range(2):
  for effect in [4,5,6,7,8,9,10,0,1,2,3]:
   for closing in (0,1):
    p.put('gLwImage',image);p.put('gLwEffect',effect);p.put('gLwClosing',closing);p.put('gLwTestReset',1);p.request();pages=p.pages();back=p.raw(pages[2],32000)
    for page in (0,1):assert p.raw(pages[page],32000)==expected(back,image,effect,closing,0);report['full_buffer_checks']+=1
    # Every original-width 16px step, every fold row and all block-batch boundaries;
    # repeated targets check pause/catch-up; forward jumps test missed page updates.
    limit=LIMITS[effect];speed=SPEEDS[effect]
    targets=list(range(1,limit+1))if effect in (1,7) else list(range(speed,limit+1,speed))
    targets=sorted(targets+[limit//2,limit//2,limit,limit]+(list(range(1,34,2)) if effect>=9 else []))
    nextpage=1
    for i,target in enumerate(targets):
     page=nextpage;nextpage^=1;p.put('gLwTarget',target);p.request();actual=p.raw(pages[page],32000);ref=expected(back,image,effect,closing,target);errors=sum(a!=b for a,b in zip(actual,ref));assert not errors,(image,effect,closing,target,page,errors)
     report['full_buffer_checks']+=1
     if effect==5:assert p.raw(0xff8240,32)==expected_palette(image,effect,closing,target)
     if image==0 and not closing and target==targets[len(targets)//2]:p.preview(pages[page],image,f'preview-{NAMES[effect]}.png',expected_palette(image,effect,closing,target))
    p.put('gLwTarget',limit);p.request()
    for page in (0,1):assert p.raw(pages[page],32000)==expected(back,image,effect,closing,limit);report['full_buffer_checks']+=1
    report['cases'].append({'image':image,'effect':NAMES[effect],'closing':closing,'targets':len(targets)})
    print('PASS',image,NAMES[effect],'close'if closing else'open',flush=True)
 # Resume the real loop, including the palette swap while both pages are black.
 p.put('gLwHold',0);p.waitval('gLwPhase',0);h.wait(.1)
 live=[]
 for effect in range(len(NAMES)):
  select(p,effect);assert p.val('gLwEffect')==effect
  before=p.val('gLwImage');p.put('gLwHoldOnBlack',1);h.tap('N',hold=.05,after=.08);p.waitval('gLwAtBlack',1)
  pages=p.pages()
  for page in (0,1):assert p.raw(pages[page]+24*160,25600)==bytes(25600)
  assert p.raw(0xff8240,32)==expected_palette(before,effect,1,LIMITS[effect]),('old palette',effect)
  # Selecting another mode while a transition owns its histories is ignored.
  h.tap('RIGHT',hold=.04,after=.06);assert p.val('gLwEffect')==effect
  p.put('gLwHoldOnBlack',0);p.waitval('gLwPhase',0);h.wait(.1);assert p.val('gLwImage')==before^1
  pages=p.pages()
  for page in (0,1):assert p.raw(pages[page]+24*160,25600)==PICTURES[before^1]
  assert p.raw(0xff8240,32)==PALETTES[before^1],('new palette',effect)
  live.append({'effect':NAMES[effect],'black_both_pages':True,'palette_before_after':True,'final_image_both_pages':True})
 # Pause at the start of a new closing pass; neither progress nor picture changes.
 h.tap('SPACE',hold=.05,after=.06);assert p.val('gLwPaused')==1;h.tap('N',hold=.05,after=.08);p.waitval('gLwPhase',1);t=p.val('gLwTarget');h.wait(.2);assert p.val('gLwTarget')==t;assert t==0
 h.tap('SPACE',hold=.05,after=.08);p.waitval('gLwPhase',0)
 h.control('hatari-event keydown 01');h.wait(.12);h.control('hatari-event keyup 01');h.wait(.15);assert p.val('gLwExited')==1
 report.update({'live_cycles':live,'all_11_modes':True,'palette_stage_checks':True,'pause_and_controls':True,'clean_exit':True,'machine':'STE 68000 8 MHz PAL, 1 MiB, German TOS 1.62','release_sha256':hashlib.sha256((APP/'LCKWIPE.PRG').read_bytes()).hexdigest()});(APP/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print(report['full_buffer_checks'],'full native buffers passed',flush=True)
