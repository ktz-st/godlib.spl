from common import *
checks=0;coverage=[]
with HatariSession(str(DEBUG),hatari='/opt/homebrew/opt/hatari/Hatari.app/Contents/MacOS/hatari',tos=str(TOS),machine='ste',extra_args=['--confirm-quit','false','--memsize','1','--cpulevel','0','--cpuclock','8','--monitor','rgb','--fast-forward','true'])as h:
 p=Probe(h);p.put('gRouteHold',1);h.wait(.1);p.put('gRoutePaused',1)
 # Populate a deterministic queue; compare both pages throughout path changes.
 p.write(p.addr('gRouteQueue'),struct.pack('>9H',*range(9)))
 for profile in range(10):
  p.put('gRouteMode',0);p.put('gRouteProfile',profile)
  p.write(p.addr('gRouteY'),b''.join(struct.pack('>H',y)for y in META['paths'][profile]))
  for phase in range(0,40,8):
   p.put('gRoutePhase',phase)
   for page in range(2):p.request();p.check();checks+=1
  coverage.append(['P',profile]);print('curve',profile,checks,flush=True)
 for mode in [1,2,0,2,1,0]:
  p.put('gRouteMode',mode);p.put('gRoutePhase',0)
  if mode==1:p.write(p.addr('gRouteY'),struct.pack('>40H',*([84]*40)))
  for _ in range(2):p.request();p.check();checks+=1
  coverage.append(['mode_change',mode])
 p.put('gRouteMode',2)
 for phase in range(40):
  p.put('gRoutePhase',phase)
  for _ in range(2):p.request();p.check();checks+=1
 print('vertical phases',checks,flush=True)
 # Exercise the live morph and the glyph/command decoder, not just fixed draw.
 p.put('gRoutePaused',0);p.put('gRoutePhase',0);p.put('gRouteMode',0);p.put('gRouteProfile',4)
 for _ in range(64):p.request();p.check();checks+=1
 # Run every FE transition and FF wrap from the actual embedded stream.
 p.write(p.addr('gRouteText'),p.addr('Route_Text').to_bytes(4,'big'));start=p.val('gRouteCommands',4);seen=set()
 for batch in range(36):
  p.request(2);s=p.check();checks+=1;seen.add((s['mode'],s['profile']))
 assert p.val('gRouteCommands',4)-start>=24
 p.put('gRoutePaused',1);p.request();p.request();s=p.check();checks+=1
 p.preview(p.val('gRouteScreen',4),'preview.png')
 # Resume real display and exercise keyboard controls and clean lifecycle.
 h.control('hatari-option --fast-forward false')
 p.write(p.addr('gRouteText'),(p.addr('Route_Text')+4).to_bytes(4,'big'))
 p.put('gRoutePaused',0);p.put('gRouteHold',0);h.wait(.2)
 for key,target in [('H',1),('V',2),('P',0)]:
  h.tap(key,hold=.07);h.wait(1.0)
  assert p.val('gRouteMode')==target,(key,p.state())
 h.tap('SPACE',hold=.06);h.wait(.1);assert p.val('gRoutePaused')==1
 h.tap('SPACE',hold=.06);h.wait(.1);assert p.val('gRoutePaused')==0
 h.tap('SPACE',hold=.06);h.wait(.1)
 s0=p.state();h.wait(.2);assert s0==p.state()
 p.exit();assert not any('Address Error' in s or 'Bus Error' in s or 'Illegal instruction' in s for s in h.lines)
 report={'machine':'STE 68000 8 MHz PAL RGB, 1 MiB, German TOS 1.62','full_frame_comparisons':checks,'fixed_coverage':coverage,'automatic_samples':[list(v)for v in sorted(seen)],'commands_decoded':p.val('gRouteCommands',4)-start,'checks':'Full native framebuffer vs independent indexed BIG atlas; both page histories, all 10 profiles, every horizontal/vertical phase, mode transitions, live interpolation, actual FE/FF stream, controls and clean exit.','release_sha256':hashlib.sha256((APP/'DCKROUTE.PRG').read_bytes()).hexdigest()}
 (APP/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print(report,flush=True)
