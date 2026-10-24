from common import *

release=(APP/'DCKTAPIS.PRG').read_bytes();symbols=Path(os.environ.get('TP_SYMBOLS','/tmp/TPREL.PRG')).read_bytes();t,d=struct.unpack_from('>2I',release,2)
assert symbols[28+0xa0:28+t+d]==release[28+0xa0:28+t+d]
assert DEBUG.read_bytes()==release,'Run the shipped PRG with external symbols.'
machine=os.environ.get('TP_MACHINE','ste');checks=0;palchecks=0
with HatariSession(str(DEBUG),machine=machine,hatari='/opt/homebrew/opt/hatari/Hatari.app/Contents/MacOS/hatari',tos=str(TOS),extra_args=['--confirm-quit','false','--memsize','1','--cpulevel','0','--cpuclock','8','--monitor','rgb','--fast-forward','true']) as h:
 p=Probe(h);old_vector=p.val('gVblOldHandler',4)
 count=struct.unpack_from('>H',p.data('gVbl',8),6)[0];callbacks=struct.unpack('>'+str(count)+'I',p.raw(p.addr('gVbl')+20,count*4));assert callbacks.count(p.addr('Tp_Vbl'))==1
 h.tap('SPACE',hold=.04,after=.1);assert p.val('gTpControl')&1
 phase=p.val('gTpPhase');tick=p.val('gTpTicks',4);h.wait(.1);assert p.val('gTpPhase')==phase and p.val('gTpTicks',4)>tick
 pages=p.pages()
 for key,rate in [('1',0),('2',1),('3',2)]:
  h.tap(key,hold=.04,after=.08);c=p.val('gTpControl');assert (c>>2)&3==rate and p.val('gTpLatched')==c
  back=p.raw(pages[2],32000)
  for page in (0,1):assert p.raw(pages[page],32000)==back;checks+=1
  for y in range(200):
   if not (64<=y<72 or 80<=y<88 or 184<=y<200):assert back[y*160:(y+1)*160]==PICTURE[y*160:(y+1)*160]
 for reverse in (0,1):
  if reverse:h.tap('D',hold=.04,after=.08)
  assert bool(p.val('gTpControl')&2)==bool(reverse)
  for _ in range(14):
   h.tap('N',hold=.025,after=.035);phase=(phase+(-1 if reverse else 1))%14;assert p.val('gTpPhase')==phase
   actual=p.raw(0xff8240,32)
   if machine=='ste':assert actual==PALETTES[phase]
   else:assert [w&0x777 for w in struct.unpack('>16H',actual)]==[w&0x777 for w in struct.unpack('>16H',PALETTES[phase])]
   palchecks+=1
 h.tap('SPACE',hold=.04,after=.08);assert not p.val('gTpControl')&1
 h.control('hatari-event keydown 01');h.wait(.12);h.control('hatari-event keyup 01');h.wait(.25)
 assert p.val('gTpExited')==1 and p.val('gTpAttached')==0
 tick=p.val('gTpTicks',4);h.wait(.4);assert p.val('gTpTicks',4)==tick and int.from_bytes(p.raw(0x70,4),'big')==old_vector
 result={'actual_shipped_prg_tested':True,'code_data_matches_external_symbols':True,'direct_asm_vbl_callback_installed':True,'machine':machine,'ram_mib':1,'full_buffer_checks':checks,'palette_checks':palchecks,'all_rates_directions_pause_step_resume':True,'original_picture_preserved':True,'callback_detached':True,'vbl_vector_restored':True,'no_ticks_after_exit':True,'release_sha256':hashlib.sha256(release).hexdigest()}
 (APP/('release-smoke-st.json' if machine=='st' else 'release-smoke.json')).write_text(json.dumps(result,indent=2)+'\n');print(result)
