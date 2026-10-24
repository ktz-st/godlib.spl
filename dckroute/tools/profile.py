from common import *
from hrdb_profile import Rdb,profile_lines
profiles=[]
with HatariSession(str(DEBUG),hatari='/opt/homebrew/opt/hatari-hrdb/Applications/hatari-hrdb/Hatari-HRDB.app/Contents/MacOS/Hatari',tos=str(TOS),machine='ste',extra_args=['--confirm-quit','false','--memsize','1','--cpulevel','0','--cpuclock','8','--monitor','rgb','--fast-forward','true'])as h:
 p=Probe(h);p.put('gRouteHold',1);h.wait(.1);rdb=Rdb(port=int(os.environ.get('DR_HRDB_PORT','56001')))
 cases=[('curve',0,2,2,0,128),('horizontal',1,2,2,0,128),('vertical',2,2,2,0,128),('curve_morph',0,4,9,0,128),('curve_to_vertical',2,2,2,1,1),('vertical_to_curve',0,2,2,1,1)]
 for name,mode,profile,oldpath,paused,count in cases:
  p.put('gRouteMode',mode);p.put('gRouteProfile',profile);p.put('gRoutePhase',0);p.put('gRouteRequest',0);p.put('gRoutePaused',paused)
  # 128 updates consume <=26 plain glyphs, never reaching the next command.
  p.write(p.addr('gRouteText'),(p.addr('Route_Text')+4).to_bytes(4,'big'))
  path=META['paths'][oldpath]if mode!=1 else[84]*40
  p.write(p.addr('gRouteY'),struct.pack('>40H',*path));p.request();p.request()
  if name=='curve_to_vertical':
   p.write(p.addr('gRoutePreviousMode'),struct.pack('>2H',0,0))
   p.write(p.addr('gRoutePreviousY'),struct.pack('>80H',*(path*2)))
  if name=='vertical_to_curve':p.write(p.addr('gRoutePreviousMode'),struct.pack('>2H',2,2))
  if name=='curve_morph':
   p.write(p.addr('gRouteY'),struct.pack('>40H',*META['paths'][oldpath]))
   p.write(p.addr('gRoutePreviousY'),struct.pack('>80H',*(META['paths'][oldpath]*2)))
  rdb.cmd('break',wait=.12);rdb.cmd(f'memset {p.addr("gRouteCompleted"):x} 2 0000',wait=.03);rdb.cmd(f'memset {p.addr("gRouteBenchRequest"):x} 2 {1 if count==1 else 2:04x}',wait=.03)
  rdb.take('!profile');rdb.cmd('profile 1',wait=.05);rdb.take('!profile');rdb.cmd('run',wait=.05);h.wait(.7);rdb.cmd('break',wait=.2)
  msg=rdb.take('!profile')
  for _ in range(10):
   if msg:break
   rdb.pump(.2);msg=rdb.take('!profile')
  rows=profile_lines(msg);assert rows,(name,'empty profile')
  calls=sum(n for pc,n,c in rows if pc==p.addr('Route_Frame'));assert calls==count,(name,calls,count)
  # Exclude Route_Init/decoder at startup; NextGlyph decoder is before Frame.
  ranges={'advance_and_decoder':[(p.addr('Route_Init')+0,p.addr('Route_Frame')),(p.addr('Route_Advance'),p.addr('Route_Erase'))], 'erase':[(p.addr('Route_Erase'),p.addr('Route_Draw'))], 'draw':[(p.addr('Route_Draw'),p.addr('Route_RuntimeEnd'))], 'frame_dispatch':[(p.addr('Route_Frame'),p.addr('Route_Advance'))]}
  totals={k:sum(c for pc,n,c in rows if any(lo<=pc<hi for lo,hi in spans))/count for k,spans in ranges.items()};cycles=sum(totals.values())
  assert cycles>1000
  rdb.cmd('profile 0',wait=.04);rdb.cmd('run',wait=.04);assert p.val('gRouteCalls',4)==count
  item={'case':name,'frames':count,'cycles_per_update':cycles,'components':totals,'ms_at_8mhz':cycles/8000,'pal_frame_percent':cycles/1600};profiles.append(item);print(item,flush=True)
 rdb.s.close();p.put('gRoutePaused',0);p.put('gRouteHold',0);h.wait(.2)
 f0=p.val('gRouteFrames',4);m0=p.val('gRouteMissedVbl',4);h.wait(2);frames=p.val('gRouteFrames',4)-f0;missed=p.val('gRouteMissedVbl',4)-m0
 cadence={'frames':frames,'missed_vbls':missed,'fps':50*frames/(frames+missed)};p.exit()
 report={'machine':'STE 68000 8 MHz PAL RGB, 1 MiB, German TOS 1.62','scope':'ASM advance, FE/FF decoder, erase and draw. Includes register saves and dispatch; excludes C captions/input, Screen_Update and VBL/OS. CPU only, no BLiTTER. Steady modes use 128 updates; morph is a 128-update window including the remaining settled updates; mode switches are single first frames.','profiles':profiles,'normal_cadence':cadence,'release_sha256':hashlib.sha256((APP/'DCKROUTE.PRG').read_bytes()).hexdigest(),'debug_sha256':hashlib.sha256(DEBUG.read_bytes()).hexdigest()}
 (APP/'profiling.json').write_text(json.dumps(report,indent=2)+'\n');print(cadence,flush=True)
