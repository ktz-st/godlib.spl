from common import *
from hrdb_profile import Rdb,profile_lines

profiles=[]
parts=['Wipe_Update','Wipe_In_Render','Wipe_Out_Render','Wipe_In_Render_BLT','Wipe_Out_Render_BLT','Wipe_BlitFrame','Wipe_BlitWait']
with HatariSession(str(staged()),hatari='/opt/homebrew/opt/hatari-hrdb/Applications/hatari-hrdb/Hatari-HRDB.app/Contents/MacOS/Hatari',tos=str(TOS),extra_args=['--confirm-quit','false','--memsize','1','--cpulevel','0','--cpuclock','8','--monitor','rgb','--fast-forward','true']) as h:
 p=Probe(h);p.put('gWipeBenchHold',1);h.wait(.08);rdb=Rdb(port=int(os.environ.get('WIPE_HRDB_PORT','56001')))
 for backend in (0,1):
  for closing in (0,1):
   p.put('gWipeBenchBackend',backend);p.put('gWipeBenchClosing',closing)
   rdb.cmd('break',wait=.12);rdb.cmd(f'memset {p.addr("gWipeBenchDone"):x} 2 0000',wait=.03);rdb.cmd(f'memset {p.addr("gWipeBenchRequest"):x} 2 0002',wait=.03)
   rdb.take('!profile');rdb.cmd('profile 1',wait=.06);rdb.take('!profile');rdb.cmd('run',wait=.06);h.wait(8);rdb.cmd('break',wait=.2)
   message=rdb.take('!profile')
   for _ in range(10):
    if message:break
    rdb.pump(.2);message=rdb.take('!profile')
   rows=profile_lines(message);assert rows,'empty profile'
   calls={part:sum(n for pc,n,c in rows if pc==p.addr(part)) for part in parts}
   assert calls['Wipe_Update']==sum(COUNTS)==589,calls
   active=('Wipe_Out_Render' if closing else 'Wipe_In_Render')+('_BLT' if backend else '')
   assert calls[active]==589,calls
   assert sum(calls[name] for name in ['Wipe_In_Render','Wipe_Out_Render','Wipe_In_Render_BLT','Wipe_Out_Render_BLT'])==589,calls
   assert calls['Wipe_BlitFrame']==(589 if backend else 0)
   totals={part:sum(c for pc,n,c in rows if p.addr(part)<=pc<p.addr(part+'End')) for part in parts}
   cycles=sum(totals.values())/589
   rdb.cmd('profile 0',wait=.04);rdb.cmd('run',wait=.04)
   assert p.val('gWipeBenchDone')==2 and p.val('gWipeBenchCalls',4)==589 and p.val('gWipeBenchActual')==backend and p.val('gWipeBenchFinished')==1
   item={'backend':'blitter' if backend else 'cpu','direction':'out' if closing else 'in','effects':39,'updates':589,'kernel_calls':calls,'cycles_per_update':cycles,'components_per_update':{k:v/589 for k,v in totals.items()},'pal_frame_percent':cycles/1600,'ms_at_8mhz':cycles/8000,'scope':'Complete Wipe_Update dispatch + selected renderer + shared blitter setup/wait, including HOG bus stalls. Excludes init/seed, setter, presentation copy, captions, Screen_Update/VBL/OS.'}
   profiles.append(item);print(item,flush=True)
 rdb.s.close()
 p.put('gWipeBenchBackend',1);p.request(4);p.put('gWipeBenchHold',0);h.wait(.12)
 old_vector=p.val('gVblOldHandler',4);h.control('hatari-event keydown 01');h.wait(.12);h.control('hatari-event keyup 01');h.wait(.3)
 assert p.val('gWipeExited')==1 and int.from_bytes(p.raw(0x70,4),'big')==old_vector
 report={'machine':'STE MC68000 8 MHz PAL RGB, 1 MiB, German TOS 1.62','profiles':profiles,'release_sha256':hashlib.sha256((APP/'WIPE.PRG').read_bytes()).hexdigest(),'debug_sha256':hashlib.sha256(DEBUG.read_bytes()).hexdigest(),'godlib_archive_sha256':hashlib.sha256((APP.parents[1]/'godlib/libgod.a').read_bytes()).hexdigest()}
 (APP/'profiling.json').write_text(json.dumps(report,indent=2)+'\n')
