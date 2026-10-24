from common import *
from hrdb_profile import Rdb,profile_lines

profiles=[];cadence=[]
with HatariSession(str(DEBUG),hatari='/opt/homebrew/opt/hatari-hrdb/Applications/hatari-hrdb/Hatari-HRDB.app/Contents/MacOS/Hatari',tos=str(TOS),extra_args=['--confirm-quit','false','--memsize','1','--cpulevel','0','--cpuclock','8','--monitor','rgb','--fast-forward','true']) as h:
 p=Probe(h);p.put('gDwHold',1);h.wait(.08);rdb=Rdb(port=int(os.environ.get('DW_HRDB_PORT','56001')))
 for mode,mask in enumerate(MASKS):
  p.put('gDwMode',mode);p.put('gDwMask',mask);p.put('gDwPhase',0);p.put('gDwPaused',0);p.put('gDwReset',1);p.request()
  p.request(2) # settle both page histories before the measured two wave cycles
  assert p.val('gDwPhase')==0
  for paused in (0,1):
   p.put('gDwPaused',paused)
   if paused:
    p.request();p.request() # let both pages reach the fixed target first
   rdb.cmd('break',wait=.12)
   rdb.cmd(f'memset {p.addr("gDwCompleted"):x} 2 0000',wait=.03);rdb.cmd(f'memset {p.addr("gDwRequest"):x} 2 0002',wait=.03)
   rdb.take('!profile');rdb.cmd('profile 1',wait=.06);rdb.take('!profile');rdb.cmd('run',wait=.06);h.wait(.8);rdb.cmd('break',wait=.2)
   message=rdb.take('!profile')
   for _ in range(10):
    if message:break
    rdb.pump(.2);message=rdb.take('!profile')
   rows=profile_lines(message);assert rows,('empty profile',mode,paused)
   frames=sum(n for pc,n,c in rows if pc==p.addr('Dw_Frame'));assert frames==512,frames
   plane_calls=sum(n for pc,n,c in rows if pc==p.addr('Dw_Plane'));assert plane_calls==(0 if paused else 512*mask.bit_count()),plane_calls
   totals={name:sum(c for pc,n,c in rows if p.addr('Dw_'+name)<=pc<p.addr('Dw_'+name+'End')) for name in ['Frame','Select','Draw','Plane']}
   cycles=sum(totals.values())/frames
   item={'mode':NAMES[mode],'mask':mask,'paused':bool(paused),'frames':frames,'plane_calls':plane_calls,'cycles_per_update':cycles,'components_per_update':{k:v/frames for k,v in totals.items()},'pal_frame_percent':cycles/1600,'ms_at_8mhz':cycles/8000}
   rdb.cmd('profile 0',wait=.04);rdb.cmd('run',wait=.04);assert p.val('gDwCompleted')==2 and p.val('gDwCalls',4)==512;assert p.val('gDwPhase')==0
   assert struct.unpack('>2H',p.data('gDwPreviousMask',4))==(mask,mask)
   profiles.append(item);print(item,flush=True)
  p.put('gDwPaused',0)
 rdb.s.close();p.put('gDwHold',0);h.wait(.2)
 for mode in range(3):
  h.tap(str(mode+1),hold=.05,after=.2)
  assert p.val('gDwMode')==mode
  f0=p.val('gDwFrames',4);m0=p.val('gDwMissedVbl',4);h.wait(.6)
  frames=p.val('gDwFrames',4)-f0;missed=p.val('gDwMissedVbl',4)-m0
  cadence.append({'mode':NAMES[mode],'frames':frames,'missed_vbls':missed,'fps':50*frames/(frames+missed)})
 h.control('hatari-event keydown 01');h.wait(.1);h.control('hatari-event keyup 01');h.wait(.15);assert p.val('gDwExited')==1
 report={'machine':'STE 68000 8 MHz PAL RGB, 1 MiB, German TOS 1.62','scope':'ASM Dw_Frame, Dw_Select, Dw_Draw and Dw_Plane; 512 steady updates, two complete phase cycles. Excludes reset/show, header, input, C Target selection, Screen_Update and VBL/OS. CPU only, no BLiTTER.','profiles':profiles,'normal_cadence':cadence,'release_sha256':hashlib.sha256((APP/'DCKWAVE.PRG').read_bytes()).hexdigest(),'debug_sha256':hashlib.sha256(DEBUG.read_bytes()).hexdigest()}
 (APP/'profiling.json').write_text(json.dumps(report,indent=2)+'\n');print('Cadence',cadence,flush=True)
