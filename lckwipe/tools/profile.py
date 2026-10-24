from common import *
from hrdb_profile import Rdb,profile_lines
profiles=[];live=[]
with HatariSession(str(DEBUG),hatari='/opt/homebrew/opt/hatari-hrdb/Applications/hatari-hrdb/Hatari-HRDB.app/Contents/MacOS/Hatari',tos=str(TOS),extra_args=['--confirm-quit','false','--memsize','1','--cpulevel','0','--cpuclock','8','--monitor','rgb','--fast-forward','true'])as h:
 p=Probe(h);p.put('gLwHold',1);h.wait(.1);rdb=Rdb(port=int(os.environ.get('LW_HRDB_PORT','56001')))
 for effect,name in enumerate(['Lw_Spiral','Lw_Fold','Lw_Lines','Lw_Snake','Lw_Instant','Lw_Colours','Lw_Centre','Lw_Smear','Lw_InterRows','Lw_CurtainCols','Lw_InterCols']):
  for closing in (0,1):
   p.put('gLwImage',0);p.put('gLwEffect',effect);p.put('gLwClosing',closing);p.put('gLwTestReset',1);p.request()
   rdb.cmd('break',wait=.12);rdb.cmd(f'memset {p.addr("gLwCompleted"):x} 2 0000',wait=.03);rdb.cmd(f'memset {p.addr("gLwRequest"):x} 2 0002',wait=.03);rdb.take('!profile');rdb.cmd('profile 1',wait=.06);rdb.take('!profile');rdb.cmd('run',wait=.06);h.wait(.6);rdb.cmd('break',wait=.2)
   message=rdb.take('!profile')
   for _ in range(10):
    if message:break
    rdb.pump(.2);message=rdb.take('!profile')
   rows=profile_lines(message)
   if not rows:
    (p.tmp/'empty-profile.json').write_text(json.dumps({'message':message,'messages':rdb.msgs,'log':h.lines[-40:]},default=str))
    raise RuntimeError(('empty profile',effect,closing,p.tmp,message))
   frames=sum(n for pc,n,c in rows if pc==p.addr('Lw_Render'));assert frames==phase_calls(effect),frames
   calls=sum(n for pc,n,c in rows if pc==p.addr(name));assert calls==frames
   dispatch=sum(c for pc,n,c in rows if p.addr('Lw_Render')<=pc<p.addr('Lw_RenderEnd'))
   helpers={4:['Lw_Full'],5:['Lw_Full','Lw_PaletteSelect'],6:['Lw_RowList'],7:['Lw_Full'],8:['Lw_RowList'],9:['Lw_Columns'],10:['Lw_Columns']}.get(effect,[])
   drawing=sum(c for pc,n,c in rows if any(p.addr(part)<=pc<p.addr(part+'End') for part in [name]+helpers))
   item={'effect':NAMES[effect],'direction':'close'if closing else'open','updates':frames,'cycles_per_update':(dispatch+drawing)/frames,'pal_frame_percent':(dispatch+drawing)/frames/1600,'ms_at_8mhz':(dispatch+drawing)/frames/8000,'cycles_total':dispatch+drawing,'dispatch_cycles':dispatch,'drawing_cycles':drawing}
   rdb.cmd('profile 0',wait=.04);rdb.cmd('run',wait=.04);assert p.val('gLwCompleted')==2;assert struct.unpack('>2H',p.data('gLwPrevious',4))==(LIMITS[effect],LIMITS[effect]);profiles.append(item);print(item,flush=True)
 rdb.s.close();p.put('gLwHold',0);p.waitval('gLwPhase',0)
 for effect in range(len(NAMES)):
  select(p,effect);assert p.val('gLwEffect')==effect
  before=p.val('gLwTransitions',4);f0=p.val('gLwFrames',4);m0=p.val('gLwMissedVbl',4);h.tap('N',hold=.05,after=.1)
  for _ in range(100):
   if p.val('gLwTransitions',4)==before+1:break
   h.wait(.02)
  assert p.val('gLwTransitions',4)==before+1;p.waitval('gLwPhase',0);h.wait(.08)
  frames=p.val('gLwFrames',4)-f0;missed=p.val('gLwMissedVbl',4)-m0;live.append({'effect':NAMES[effect],'completed_cycles':1,'normal_frames_in_window':frames,'missed_vbls':missed,'fps':50*frames/(frames+missed)})
 h.control('hatari-event keydown 01');h.wait(.1);h.control('hatari-event keyup 01');h.wait(.15);assert p.val('gLwExited')==1
 report={'machine':'STE 68000 8 MHz PAL RGB, 1 MiB, German TOS 1.62','scope':'Only ASM Lw_Render dispatch and active pixel kernel, complete phase with per-page catch-up; includes shared full/row/column kernels and colour stage selection; excludes init/show, C Advance/Publish, header/input, hardware VBL palette writes, Screen_Update and VBL/OS. CPU only, no BLiTTER.','profiles':profiles,'normal_cadence':live,'release_sha256':hashlib.sha256((APP/'LCKWIPE.PRG').read_bytes()).hexdigest(),'debug_sha256':hashlib.sha256(DEBUG.read_bytes()).hexdigest()};(APP/'profiling.json').write_text(json.dumps(report,indent=2)+'\n');print('Cadence',live,flush=True)
