from common import *
from hrdb_profile import Rdb,profile_lines
profiles=[];cadence=[]
with HatariSession(str(DEBUG),hatari='/opt/homebrew/opt/hatari-hrdb/Applications/hatari-hrdb/Hatari-HRDB.app/Contents/MacOS/Hatari',tos=str(TOS),machine='ste',extra_args=['--confirm-quit','false','--memsize','1','--cpulevel','0','--cpuclock','8','--monitor','rgb','--fast-forward','true'])as h:
 p=Probe(h);p.put('gDbHold',1);h.wait(.05);rdb=Rdb(port=int(os.environ.get('DB_HRDB_PORT','56001')))
 cases=[(m,mask,0)for m in range(5)for mask in MASKS]+[(m,15,1)for m in range(5)]
 for mode,mask,paused in cases:
  p.put('gDbMode',mode);p.put('gDbMask',mask);p.put('gDbPaused',paused);p.put('gDbReset',1);p.request();p.request()
  start=p.val('gDbPhase')
  rdb.cmd('break',wait=.1);rdb.cmd(f'memset {p.addr("gDbCompleted"):x} 2 0000',wait=.025);rdb.cmd(f'memset {p.addr("gDbRequest"):x} 2 0002',wait=.025)
  rdb.take('!profile');rdb.cmd('profile 1',wait=.04);rdb.take('!profile');rdb.cmd('run',wait=.04);h.wait(.8);rdb.cmd('break',wait=.18)
  msg=rdb.take('!profile')
  for _ in range(10):
   if msg:break
   rdb.pump(.15);msg=rdb.take('!profile')
  rows=profile_lines(msg);assert rows,('empty',mode,mask,paused)
  calls=sum(n for pc,n,c in rows if pc==p.addr('Db_Frame'));assert calls==320,calls
  copies=sum(n for pc,n,c in rows if pc==p.addr('Db_Copy'))
  assert copies==(0 if paused else {0:640,1:3200,2:1280,3:638,4:400}[mode]),(mode,paused,copies)
  components={name:sum(c for pc,n,c in rows if p.addr('Db_'+name)<=pc<p.addr('Db_'+name+'End'))/320 for name in['Frame','Prepare','Execute','Copy']}
  components['row_kernels']=sum(c for pc,n,c in rows if p.addr('Db_RowsStart')<=pc<p.addr('Db_RowsEnd'))/320
  cycles=sum(components.values());assert cycles>0
  rdb.cmd('profile 0',wait=.035);rdb.cmd('run',wait=.035);assert p.val('gDbCompleted')==2 and p.val('gDbCalls',4)==320 and p.val('gDbPhase')==start
  item={'mode':NAMES[mode],'mask':mask,'paused':bool(paused),'updates':320,'copy_commands':copies,'cycles_per_update':cycles,'components':components,'ms_at_8mhz':cycles/8000,'pal_frame_percent':cycles/1600};profiles.append(item);print(item,flush=True)
 rdb.s.close();p.put('gDbPaused',0);p.put('gDbMask',15);p.put('gDbHold',0);h.wait(.15)
 for mode in range(5):
  p.key(mode+2);assert p.val('gDbMode')==mode;h.wait(.1)
  f0=p.val('gDbFrames',4);m0=p.val('gDbMissedVbl',4);h.wait(.65);frames=p.val('gDbFrames',4)-f0;missed=p.val('gDbMissedVbl',4)-m0
  item={'mode':NAMES[mode],'mask':15,'frames':frames,'missed_vbls':missed,'fps':50*frames/(frames+missed)};cadence.append(item);print(item,flush=True)
 p.exit()
 report={'machine':'STE 68000 8 MHz PAL RGB, 1 MiB, German TOS 1.62','scope':'Db_Frame/Prepare/Execute/Copy and all row kernels. Includes building commands, per-page restoration, movement and register saves; excludes C headers/input, Screen_Update and VBL/OS. 320 updates = two whole 160-step cycles. Strips average actual redraws and unchanged pages; paused modes include two settled pages and intentionally execute no copy commands. CPU only, no BLiTTER.','profiles':profiles,'normal_cadence':cadence,'release_sha256':hashlib.sha256((APP/'DCKBLOCK.PRG').read_bytes()).hexdigest(),'debug_sha256':hashlib.sha256(DEBUG.read_bytes()).hexdigest()}
 (APP/'profiling.json').write_text(json.dumps(report,indent=2)+'\n')
