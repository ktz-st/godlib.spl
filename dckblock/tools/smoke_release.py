from common import *
release=(APP/'DCKBLOCK.PRG').read_bytes();symbols=Path(os.environ.get('DB_SYMBOLS','/tmp/DBREL.PRG')).read_bytes();t,d=struct.unpack_from('>2I',release,2)
assert symbols[28+0xa0:28+t+d]==release[28+0xa0:28+t+d]
machine=os.environ.get('DB_MACHINE','ste');checks=0;cadence=[]
with HatariSession(str(APP/'DCKBLOCK.PRG'),hatari='/opt/homebrew/opt/hatari/Hatari.app/Contents/MacOS/hatari',tos=str(TOS),machine=machine,extra_args=['--confirm-quit','false','--memsize','1','--cpulevel','0','--cpuclock','8','--blitter','false','--monitor','rgb','--fast-forward','true'])as h:
 p=Probe(h);old_vector=p.val('gVblOldHandler',4)
 p.key(57);assert p.val('gDbPaused')==1;mask_index=0
 for mode in range(5):
  p.key(mode+2);assert p.val('gDbMode')==mode
  for mask in MASKS:
   while MASKS[mask_index]!=mask:p.key(50);mask_index=(mask_index+1)%3
   assert p.val('gDbMask')==mask
   pages=p.pages();back=p.raw(pages[2],32000);phase=p.val('gDbPhase')
   for ptr in pages[:2]:assert p.raw(ptr,32000)==expected(back,mode,mask,phase);checks+=1
   if machine=='ste'and mask in(15,2):p.preview(pages[0],f'preview-{NAMES[mode]}'+('-one'if mask==2 else'')+'.png')
   p.key(49);assert p.val('gDbPhase')==(phase+1)%160
   for ptr in pages[:2]:assert p.raw(ptr,32000)==expected(back,mode,mask,(phase+1)%160);checks+=1
   p.key(57);assert p.val('gDbPaused')==0;h.wait(.08)
   f0=p.val('gDbFrames',4);m0=p.val('gDbMissedVbl',4);h.wait(.12);frames=p.val('gDbFrames',4)-f0;missed=p.val('gDbMissedVbl',4)-m0
   cadence.append({'mode':NAMES[mode],'mask':mask,'frames':frames,'missed_vbls':missed,'fps':50*frames/(frames+missed)})
   p.key(57);assert p.val('gDbPaused')==1
 actual_pal=struct.unpack('>16H',p.raw(0xff8240,32));want_pal=struct.unpack('>16H',PALETTE);pal_mask=0x777 if machine=='st'else 0xfff
 assert [v&pal_mask for v in actual_pal]==[v&pal_mask for v in want_pal]
 assert p.raw(p.addr('Db_Picture'),25600)==PICTURE
 p.key(19);assert p.val('gDbRaster')==1
 p.key(19);assert p.val('gDbRaster')==0
 p.exit();assert int.from_bytes(p.raw(0x70,4),'big')==old_vector
 result={'actual_shipped_prg_tested':True,'external_symbols_code_data_match':True,'machine':machine,'ram_mib':1,'blitter_enabled':False,'all_5_modes_and_3_masks':True,'full_buffer_checks':checks,'pause_step_resume_mask_stripe':True,'palette_and_source_unchanged':True,'clean_exit_vbl_restored':True,'steady_cadence':cadence,'release_sha256':hashlib.sha256(release).hexdigest()}
 (APP/('release-smoke-st.json'if machine=='st'else'release-smoke.json')).write_text(json.dumps(result,indent=2)+'\n');print(result,flush=True)
