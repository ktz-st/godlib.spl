from common import *

release=(APP/'DCKWAVE.PRG').read_bytes();symbols=Path(os.environ.get('DW_SYMBOLS','/tmp/DWREL.PRG')).read_bytes();t,d=struct.unpack_from('>2I',release,2)
assert symbols[28+0xa0:28+t+d]==release[28+0xa0:28+t+d]
assert DEBUG.read_bytes()==release,'Use the shipped PRG, with DW_SYMBOLS for external symbols.'
machine=os.environ.get('DW_MACHINE','ste')
with HatariSession(str(DEBUG),machine=machine,hatari='/opt/homebrew/opt/hatari/Hatari.app/Contents/MacOS/hatari',tos=str(TOS),extra_args=['--confirm-quit','false','--memsize','1','--cpulevel','0','--cpuclock','8','--monitor','rgb','--fast-forward','true']) as h:
 p=Probe(h);h.tap('SPACE',hold=.05,after=.1);assert p.val('gDwPaused')==1
 checks=0
 for mode,mask in enumerate(MASKS):
  h.tap(str(mode+1),hold=.05,after=.12);assert p.val('gDwMode')==mode and p.val('gDwMask')==mask
  pages=p.pages();back=p.raw(pages[2],32000);phase=p.val('gDwPhase')
  for page in (0,1):assert p.raw(pages[page],32000)==expected(back,mask,phase);checks+=1
  if machine=='ste':p.preview(pages[0],f'preview-{NAMES[mode]}.png')
  h.tap('N',hold=.04,after=.1);assert p.val('gDwPhase')==(phase+1)&255
  for page in (0,1):assert p.raw(pages[page],32000)==expected(back,mask,(phase+1)&255);checks+=1
 h.tap('R',hold=.04,after=.08);assert p.val('gDwRaster')==1
 h.tap('SPACE',hold=.04,after=.1);assert p.val('gDwPaused')==0
 f=p.val('gDwFrames',4);h.wait(.15);assert p.val('gDwFrames',4)>f
 h.control('hatari-event keydown 01');h.wait(.1);h.control('hatari-event keyup 01');h.wait(.3);assert p.val('gDwExited')==1
 result={'actual_shipped_prg_tested':True,'code_data_matches_external_symbols':True,'machine':machine,'ram_mib':1,'all_modes':True,'full_buffer_checks':checks,'pause_step_resume':True,'cpu_stripe':True,'clean_exit':True,'release_sha256':hashlib.sha256(release).hexdigest()}
 (APP/('release-smoke-st.json' if machine=='st' else 'release-smoke.json')).write_text(json.dumps(result,indent=2)+'\n');print(result)
