from common import *
import hashlib
release=(APP/'DCKBOBS.PRG').read_bytes();symbols=Path(os.environ.get('BOBS_SYMBOLS','/tmp/BOBSREL.PRG'));debug=symbols.read_bytes();t,d=struct.unpack_from('>2I',release,2);assert debug[28+0xa0:28+t+d]==release[28+0xa0:28+t+d]
assert DEBUG.read_bytes()==release, 'Run this smoke test on DCKBOBS.PRG itself; use BOBS_SYMBOLS for the unstripped symbol source.'
machine=os.environ.get('BOBS_MACHINE','ste')
with HatariSession(str(DEBUG),machine=machine,hatari='/opt/homebrew/opt/hatari/Hatari.app/Contents/MacOS/hatari',tos=str(TOS),extra_args=['--confirm-quit','false','--memsize','1','--cpulevel','0','--cpuclock','8','--monitor','rgb','--fast-forward','true'])as h:
 p=Probe(h);assert p.val('gBobsCount')==4 and p.val('gBobsBlitter')==(0 if machine=='st' else 1)
 result={'actual_shipped_prg_tested':True,'code_data_matches_external_symbols':True,'ram_mib':1,'default_bobs':4,'default_blitter':bool(p.val('gBobsBlitter')),'machine':machine,'frames_start':p.val('gBobsFrames',4)}
 h.wait(.3)
 for key in ['T','P','B','B','1','2','3','2','C','SPACE']:
  h.tap(key,hold=.05,after=.1)
 assert p.val('gBobsPaused')==1;pos=p.data('gBobsPositions',32);h.wait(.1);assert pos==p.data('gBobsPositions',32)
 h.tap('SPACE',hold=.05,after=.1);assert p.val('gBobsPaused')==0
 h.control('hatari-event keydown 01');h.wait(.1);h.control('hatari-event keyup 01');h.wait(.2);assert p.val('gBobsExited')==1
 result.update({'pause_and_controls':True,'clean_exit':True,'release_sha256':hashlib.sha256(release).hexdigest()});(APP/('release-smoke-st.json'if machine=='st'else'release-smoke.json')).write_text(json.dumps(result,indent=2)+'\n');print(result)
