from common import *
from preview import make_preview

report={'vbl_records':0,'palette_mismatches':0,'cases':[],'manual_steps':0}
with HatariSession(str(DEBUG),hatari='/opt/homebrew/opt/hatari/Hatari.app/Contents/MacOS/hatari',tos=str(TOS),extra_args=['--confirm-quit','false','--memsize','1','--cpulevel','0','--cpuclock','8','--monitor','rgb','--fast-forward','true']) as h:
 p=Probe(h);p.put('gTpHoldMain',1);h.wait(.08)
 frames=p.val('gTpFrames',4);old_vector=p.val('gVblOldHandler',4)
 pages=p.pages();back=p.raw(pages[2],32000)
 for y in range(200):
  if not (64<=y<72 or 80<=y<88 or 184<=y<200):assert back[y*160:(y+1)*160]==PICTURE[y*160:(y+1)*160]
 for page in (0,1):assert p.raw(pages[page],32000)==back
 count=struct.unpack_from('>H',p.data('gVbl',8),6)[0]
 callbacks=struct.unpack('>'+str(count)+'I',p.raw(p.addr('gVbl')+20,count*4))
 assert p.val('gTpAttached')==1 and callbacks.count(p.addr('TraceVbl'))==1
 for rate in range(3):
  period=1<<rate
  for reverse in (0,1):
   control=(rate<<2)|(reverse<<1);p.put('gTpControl',control);p.waitval('gTpLatched',control)
   p.waitval('gTpLogCount',512);p.put('gTpLogCount',0);p.waitval('gTpLogCount',512)
   raw=p.data('gTpLog',512*42);records=[]
   for i in range(512):
    tick,phase,c,countdown=struct.unpack_from('>I3H',raw,i*42);pal=raw[i*42+10:(i+1)*42]
    assert c==control and 0<=phase<14 and 1<=countdown<=period,(i,tick,phase,c,countdown)
    assert pal==PALETTES[phase],(rate,reverse,i,'palette')
    records.append((tick,phase,countdown));report['vbl_records']+=1
   for previous,current in zip(records,records[1:]):
    assert current[0]==previous[0]+1
    advance=previous[2]==1;expected=(previous[1]+(-1 if reverse else 1))%14 if advance else previous[1]
    assert current[1]==expected,(rate,reverse,previous,current)
    assert current[2]==(period if advance else previous[2]-1)
   assert len({r[1] for r in records})==14
   assert p.val('gTpFrames',4)==frames,'Main loop advanced during hold'
   for page in (0,1):assert p.raw(pages[page],32000)==back
   report['cases'].append({'vbls_per_palette':period,'reverse':bool(reverse),'records':512,'all_14_phases':True,'main_loop_held':True})
   print('PASS',period,'VBL',('reverse' if reverse else 'forward'),flush=True)
 for reverse in (0,1):
  control=1|(reverse<<1)|4;p.put('gTpControl',control);p.waitval('gTpLatched',control);phase=p.val('gTpPhase');tick=p.val('gTpTicks',4);h.wait(.1)
  assert p.val('gTpPhase')==phase and p.val('gTpTicks',4)>tick
  for _ in range(14):
   control^=16;p.put('gTpControl',control);p.waitval('gTpLatched',control);phase=(phase+(-1 if reverse else 1))%14
   assert p.val('gTpPhase')==phase and p.raw(0xff8240,32)==PALETTES[phase]
   if phase in (0,6):p.preview(pages[0],phase,f'preview-{phase}.png')
   report['manual_steps']+=1
 p.put('gTpHoldMain',0);h.wait(.1)
 # Exercise actual keyboard commands, not just debug writes.
 for key,rate in [('1',0),('2',1),('3',2)]:
  h.tap(key,hold=.04,after=.08);c=p.val('gTpControl');assert (c>>2)&3==rate;p.waitval('gTpLatched',c)
 c=p.val('gTpControl');h.tap('D',hold=.04,after=.08);assert p.val('gTpControl')==c^2
 phase=p.val('gTpPhase');direction=-1 if p.val('gTpControl')&2 else 1
 h.tap('N',hold=.04,after=.08);assert p.val('gTpControl')&1 and p.val('gTpPhase')==(phase+direction)%14
 h.tap('SPACE',hold=.04,after=.08);assert not p.val('gTpControl')&1
 h.control('hatari-event keydown 01');h.wait(.1);h.control('hatari-event keyup 01');h.wait(.25)
 assert p.val('gTpExited')==1 and p.val('gTpAttached')==0
 ticks=p.val('gTpTicks',4);h.wait(.4);assert p.val('gTpTicks',4)==ticks
 assert int.from_bytes(p.raw(0x70,4),'big')==old_vector
 report.update({'original_art_preserved':True,'both_pages_static_during_vbl':True,'keyboard_controls':True,'callback_detached':True,'vbl_vector_restored':True,'clean_exit':True,'machine':'STE 68000 8 MHz PAL RGB, 1 MiB, German TOS 1.62','release_sha256':hashlib.sha256((APP/'DCKTAPIS.PRG').read_bytes()).hexdigest()})
 (APP/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print(report['vbl_records'],'VBL records and',report['manual_steps'],'manual steps passed',flush=True)
make_preview()
