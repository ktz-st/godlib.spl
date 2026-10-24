from common import *
from hrdb_profile import Rdb,profile_lines

release=(APP/'DCKTAPIS.PRG').read_bytes();assert DEBUG.read_bytes()==release,'Profile the shipped PRG with external symbols.'
profiles=[];cadence=[]
with HatariSession(str(DEBUG),hatari='/opt/homebrew/opt/hatari-hrdb/Applications/hatari-hrdb/Hatari-HRDB.app/Contents/MacOS/Hatari',tos=str(TOS),extra_args=['--confirm-quit','false','--memsize','1','--cpulevel','0','--cpuclock','8','--monitor','rgb','--fast-forward','true']) as h:
 p=Probe(h);rdb=Rdb(port=int(os.environ.get('TP_HRDB_PORT','56001')))
 for control,name in [(0,'1 VBL forward'),(4,'2 VBL forward'),(8,'4 VBL forward'),(6,'2 VBL reverse'),(5,'paused')]:
  p.put('gTpControl',control);p.waitval('gTpLatched',control);h.wait(.08)
  rdb.cmd('break',wait=.12);rdb.take('!profile');rdb.cmd('profile 1',wait=.06);rdb.take('!profile');rdb.cmd('run',wait=.06);h.wait(.7);rdb.cmd('break',wait=.2)
  message=rdb.take('!profile')
  for _ in range(10):
   if message:break
   rdb.pump(.2);message=rdb.take('!profile')
  rows=profile_lines(message);assert rows,('empty profile',name)
  calls=sum(n for pc,n,c in rows if pc==p.addr('Tp_Vbl'));assert calls>=256,calls
  writes=sum(n for pc,n,c in rows if pc==p.addr('Tp_Write'));assert writes==calls,(calls,writes)
  advances=sum(n for pc,n,c in rows if pc==p.addr('Tp_Period'))
  period=1<<((control>>2)&3)
  assert advances==0 if control&1 else abs(advances-calls/period)<=1,(control,calls,advances)
  parts={'control_and_phase':sum(c for pc,n,c in rows if p.addr('Tp_Vbl')<=pc<p.addr('Tp_Write')),'palette_write':sum(c for pc,n,c in rows if p.addr('Tp_Write')<=pc<p.addr('Tp_WriteEnd')),'period_reset':sum(c for pc,n,c in rows if p.addr('Tp_Period')<=pc<p.addr('Tp_VblEnd'))}
  cycles=sum(parts.values())/calls
  rdb.cmd('profile 0',wait=.04);rdb.cmd('run',wait=.04)
  profiles.append({'mode':name,'control':control,'vbl_calls':calls,'palette_writes':writes,'phase_advances':advances,'cycles_per_vbl':cycles,'components_per_vbl':{k:v/calls for k,v in parts.items()},'pal_frame_percent':cycles/1600,'microseconds_at_8mhz':cycles/8})
  print(profiles[-1],flush=True)
  f0=p.val('gTpFrames',4);m0=p.val('gTpMissedVbl',4);h.wait(.3);frames=p.val('gTpFrames',4)-f0;missed=p.val('gTpMissedVbl',4)-m0
  cadence.append({'mode':name,'frames':frames,'missed_vbls':missed,'fps':50*frames/(frames+missed)})
 rdb.s.close();old_vector=p.val('gVblOldHandler',4)
 h.control('hatari-event keydown 01');h.wait(.12);h.control('hatari-event keyup 01');h.wait(.25)
 assert p.val('gTpExited')==1 and p.val('gTpAttached')==0 and int.from_bytes(p.raw(0x70,4),'big')==old_vector
 report={'actual_shipped_prg_profiled':True,'machine':'STE 68000 8 MHz PAL RGB, 1 MiB, German TOS 1.62','scope':'Complete ASM Tp_Vbl callback, including phase/control, counters, period helper and all 16 hardware colour writes. Actual VBL calls, no synthetic main-loop batch. Excludes shared GodLib interrupt entry/dispatch/video updater, setup, header, input, Screen_Update and OS. No BLiTTER or HBL.','profiles':profiles,'normal_cadence':cadence,'release_sha256':hashlib.sha256(release).hexdigest()}
 (APP/'profiling.json').write_text(json.dumps(report,indent=2)+'\n');print('Cadence',cadence,flush=True)
