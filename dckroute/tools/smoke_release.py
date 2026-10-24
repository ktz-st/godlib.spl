from common import *
release=(APP/'DCKROUTE.PRG').read_bytes();symbol_file=Path('/tmp/DRREL.PRG').read_bytes();t,d=struct.unpack_from('>2I',release,2)
assert release[28+0xa0:28+t+d]==symbol_file[28+0xa0:28+t+d]
machine=os.environ.get('DR_MACHINE','ste');tested=[]
with HatariSession(str(APP/'DCKROUTE.PRG'),hatari='/opt/homebrew/opt/hatari/Hatari.app/Contents/MacOS/hatari',tos=str(TOS),machine=machine,extra_args=['--confirm-quit','false','--memsize','1','--cpulevel','0','--cpuclock','8','--blitter','false','--monitor','rgb','--fast-forward','true'])as h:
 p=Probe(h);old_vector=p.val('gVblOldHandler',4)
 # Script supplies automatic route commands. Manual changes enter at the next
 # glyph boundary. Slow down for key assertions so auto commands cannot race.
 h.control('hatari-option --fast-forward false')
 def pause(value):
  if p.val('gRoutePaused')!=value:h.tap('SPACE',hold=.06,after=.08)
  assert p.val('gRoutePaused')==value
 def capture(name):
  pause(1);h.wait(.15);s=p.state();expected=p.expected(s);pages=struct.unpack('>4I',p.data('gScreenClass',20)[4:20])
  for ptr in pages[:2]:assert p.raw(ptr+24*160,160*160)==expected[24*160:184*160],(name,s)
  p.preview(pages[0],name+('-st'if machine=='st'else'')+'.png')
  actual=struct.unpack('>16H',p.raw(0xff8240,32));expected_pal=struct.unpack('>16H',PAL)
  mask=0x777 if machine=='st'else 0xfff
  assert [v&mask for v in actual]==[v&mask for v in expected_pal]
  tested.append({'mode':s['mode'],'profile':s['profile'],'both_native_pages':True})
 capture('preview-curve')
 for key,target,name in [('H',1,'preview-horizontal'),('V',2,'preview-vertical'),('P',0,'preview-return')]:
  pause(0);h.tap(key,hold=.06,after=.04)
  for _ in range(70):
   if p.val('gRouteRequest')==0 and p.val('gRouteMode')==target:break
   h.wait(.03)
  assert p.val('gRouteMode')==target,(key,p.state());capture(name)
 pause(0);h.tap('N',hold=.06,after=.1)
 for _ in range(70):
  if p.val('gRouteRequest')==0:break
  h.wait(.03)
 assert p.val('gRouteRequest')==0
 h.tap('R',hold=.06,after=.1);assert p.val('gRouteRaster')==1
 h.tap('R',hold=.06,after=.1);assert p.val('gRouteRaster')==0
 h.control('hatari-option --fast-forward true');f0=p.val('gRouteFrames',4);m0=p.val('gRouteMissedVbl',4);h.wait(1);frames=p.val('gRouteFrames',4)-f0;missed=p.val('gRouteMissedVbl',4)-m0
 p.exit();assert int.from_bytes(p.raw(0x70,4),'big')==old_vector
 report={'actual_shipped_prg_tested':True,'external_symbols_code_data_match':True,'machine':machine,'ram_mib':1,'blitter_enabled':False,'native_frame_checks':tested,'manual_modes_and_next_pause_stripe_exit':True,'vbl_restored':True,'frames':frames,'missed_vbls':missed,'fps':50*frames/(frames+missed),'sha256':hashlib.sha256(release).hexdigest()}
 (APP/('release-smoke-st.json'if machine=='st'else'release-smoke.json')).write_text(json.dumps(report,indent=2)+'\n');print(report,flush=True)
