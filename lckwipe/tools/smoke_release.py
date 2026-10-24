from common import *
release=(APP/'LCKWIPE.PRG').read_bytes();symbols=Path(os.environ.get('LW_SYMBOLS','/tmp/LWREL.PRG')).read_bytes();t,d=struct.unpack_from('>2I',release,2)
assert symbols[28+0xa0:28+t+d]==release[28+0xa0:28+t+d]
assert DEBUG.read_bytes()==release,'Run the shipped PRG; use LW_SYMBOLS only for its external symbol names.'
machine=os.environ.get('LW_MACHINE','ste')
with HatariSession(str(DEBUG),machine=machine,hatari='/opt/homebrew/opt/hatari/Hatari.app/Contents/MacOS/hatari',tos=str(TOS),extra_args=['--confirm-quit','false','--memsize','1','--cpulevel','0','--cpuclock','8','--monitor','rgb','--fast-forward','true'])as h:
 p=Probe(h);assert p.val('gLwPhase')==0 and p.val('gLwImage')==0
 cycles=[]
 for effect in range(len(NAMES)):
  select(p,effect);assert p.val('gLwEffect')==effect
  before=p.val('gLwTransitions',4);image=p.val('gLwImage');h.tap('N',hold=.05,after=.08)
  for _ in range(100):
   if p.val('gLwTransitions',4)==before+1:break
   h.wait(.02)
  assert p.val('gLwTransitions',4)==before+1;p.waitval('gLwPhase',0);assert p.val('gLwImage')==image^1;h.wait(.05)
  for ptr in p.pages()[:2]:assert p.raw(ptr+24*160,25600)==PICTURES[image^1]
  cycles.append(NAMES[effect])
 h.tap('SPACE',hold=.05,after=.05);assert p.val('gLwPaused')==1;h.tap('N',hold=.05,after=.05);p.waitval('gLwPhase',1);assert p.val('gLwTarget')==0;h.wait(.1);assert p.val('gLwTarget')==0
 # Exiting during a paused transition still releases Screen/Platform normally.
 h.control('hatari-event keydown 01');h.wait(.1);h.control('hatari-event keyup 01');h.wait(.2);assert p.val('gLwExited')==1
 result={'actual_shipped_prg_tested':True,'code_data_matches_external_symbols':True,'machine':machine,'ram_mib':1,'cycles':cycles,'both_pages_final_images':True,'pause_at_start':True,'exit_during_transition':True,'release_sha256':hashlib.sha256(release).hexdigest()};(APP/('release-smoke-st.json'if machine=='st'else'release-smoke.json')).write_text(json.dumps(result,indent=2)+'\n');print(result)
