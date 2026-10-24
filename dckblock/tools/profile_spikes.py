"""Measure actual one-frame redraws separately from low-frequency averages."""
from common import *
from hrdb_profile import Rdb,profile_lines
results=[]
with HatariSession(str(DEBUG),hatari='/opt/homebrew/opt/hatari-hrdb/Applications/hatari-hrdb/Hatari-HRDB.app/Contents/MacOS/Hatari',tos=str(TOS),machine='ste',extra_args=['--confirm-quit','false','--memsize','1','--cpulevel','0','--cpuclock','8','--monitor','rgb','--fast-forward','true'])as h:
 p=Probe(h);p.put('gDbHold',1);p.put('gDbPaused',1);h.wait(.05);rdb=Rdb(port=int(os.environ.get('DB_HRDB_PORT','56001')))
 cases=[('strips_redraw',4,m,4,m,16,10)for m in MASKS]+[('full_to_move',3,15,0,15,0,2),('full_to_strips',3,15,4,15,16,11),('drop_three_planes',1,15,1,2,0,11)]
 for name,oldmode,oldmask,mode,mask,phase,copies_expected in cases:
  p.put('gDbMode',oldmode);p.put('gDbMask',oldmask);p.put('gDbReset',1);p.request();p.request()
  p.put('gDbMode',mode);p.put('gDbMask',mask);p.put('gDbPhase',phase)
  rdb.cmd('break',wait=.1);rdb.cmd(f'memset {p.addr("gDbCompleted"):x} 2 0000',wait=.025);rdb.cmd(f'memset {p.addr("gDbRequest"):x} 2 0001',wait=.025)
  rdb.take('!profile');rdb.cmd('profile 1',wait=.04);rdb.take('!profile');rdb.cmd('run',wait=.04);h.wait(.6);rdb.cmd('break',wait=.18);msg=rdb.take('!profile')
  for _ in range(10):
   if msg:break
   rdb.pump(.15);msg=rdb.take('!profile')
  rows=profile_lines(msg);assert rows
  assert sum(n for pc,n,c in rows if pc==p.addr('Db_Frame'))==1
  copies=sum(n for pc,n,c in rows if pc==p.addr('Db_Copy'));assert copies==copies_expected,(name,copies,copies_expected)
  cycles=sum(c for pc,n,c in rows if p.addr('Db_Frame')<=pc<p.addr('Db_CopyEnd') or p.addr('Db_RowsStart')<=pc<p.addr('Db_RowsEnd'))
  rdb.cmd('profile 0',wait=.035);rdb.cmd('run',wait=.035);assert p.val('gDbCompleted')==1 and p.val('gDbCalls',4)==1
  item={'case':name,'mode':NAMES[mode],'mask':mask,'old_mode':NAMES[oldmode],'old_mask':oldmask,'copy_commands':copies,'cycles':cycles,'ms_at_8mhz':cycles/8000,'pal_frame_percent':cycles/1600};results.append(item);print(item,flush=True)
 rdb.s.close();p.put('gDbHold',0);h.wait(.1);p.exit()
 report={'machine':'STE 68000 8 MHz PAL RGB, 1 MiB, German TOS 1.62','scope':'One ASM Db_Frame including prepare, restore and all copies, paused phase supplied by test. Excludes C header/input and Screen_Update/VBL. These are measured cases, not a maximum over all changes. A >100% frame is a one-time mode/mask transition on each page.','profiles':results,'release_sha256':hashlib.sha256((APP/'DCKBLOCK.PRG').read_bytes()).hexdigest()}
 (APP/'profile-spikes.json').write_text(json.dumps(report,indent=2)+'\n')
