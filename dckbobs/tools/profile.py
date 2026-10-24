from common import *
from hrdb_profile import Rdb,profile_lines
import hashlib,re
results=[]
# Profile complete object code for library callees, including BLiTTER stalls.
# Scene/header/setup paths in these objects are not executed in the timed batch.
maptext=Path('/tmp/BOBSDBG.map').read_text();objects={}
for obj in ['chunk_s.o','grf_4_s.o','grf_b4_s.o','blitter.o']:
 m=re.search(r'^\s+(?:CODE|\.text)\s+0x([0-9a-f]+)\s+0x([0-9a-f]+)\s+[^\n]*libgod\.a\('+re.escape(obj)+r'\)',maptext,re.M);assert m,obj;objects[obj]=(int(m[1],16),int(m[1],16)+int(m[2],16))
with HatariSession(str(DEBUG),hatari='/opt/homebrew/opt/hatari-hrdb/Applications/hatari-hrdb/Hatari-HRDB.app/Contents/MacOS/Hatari',tos=str(TOS),extra_args=['--confirm-quit','false','--memsize','4','--cpulevel','0','--cpuclock','8','--monitor','rgb','--fast-forward','true'])as h:
 p=Probe(h);p.put('gBobsHold',1);h.wait(.1);rdb=Rdb(port=int(os.environ.get('BOBS_HRDB_PORT','56001')))
 sy=p.sy;ordered=sorted(set(sy.values()));after=lambda name:next(x for x in ordered if x>sy[name])
 def cycles(rows,lo,hi):return sum(c for pc,n,c in rows if p.base+lo<=pc<p.base+hi)
 for backend in (0,1):
  for trail in (0,1):
   for count in (1,4,8):
    p.put('gBobsBlitter',backend);p.put('gBobsTrails',trail);p.put('gBobsPath',0);p.put('gBobsCount',count);p.put('gBobsPaused',0);p.put('gBobsReset',1);p.request()
    before=p.data('gBobsIndices',16)
    rdb.cmd('break',wait=.12);rdb.cmd(f'memset {p.addr("gBobsCompleted"):x} 2 0000',wait=.03);rdb.cmd(f'memset {p.addr("gBobsRequest"):x} 2 0002',wait=.03);rdb.cmd('profile 1',wait=.04);rdb.cmd('run',wait=.04);h.wait(.8);rdb.cmd('break',wait=.2)
    msg=rdb.take('!profile')
    for _ in range(10):
     if msg:break
     rdb.pump(.2);msg=rdb.take('!profile')
    rows=profile_lines(msg);assert rows
    frames=sum(n for pc,n,c in rows if pc==p.addr('Bobs_Frame'));assert frames==360,frames
    draws=sum(n for pc,n,c in rows if pc==p.addr('Graphic_4BP_DrawSprite_BLT'if backend else'Graphic_4BP_DrawSprite'));assert draws==360*count*(2 if trail else 1),(draws,count,trail)
    totals={}
    for part,name in [('trajectory','Bobs_Advance'),('restore','Bobs_Restore'),('draw','Bobs_Draw'),('store','Bobs_Store'),('dispatch','Bobs_Frame')]:totals[part]=cycles(rows,sy[name],sy[name+'End'])
    totals['restore']+=cycles(rows,*objects['chunk_s.o'])
    for obj in ['grf_4_s.o','grf_b4_s.o','blitter.o']:totals['draw']+=cycles(rows,*objects[obj])
    totals['store']+=cycles(rows,sy['Graphic_ChunkList_Store'],after('Graphic_ChunkList_Store'))
    item={'backend':'blitter'if backend else'cpu','mode':'trails'if trail else'restore','bobs':count,'frames':frames,'sprite_calls':draws,'cycles_per_frame':{k:v/frames for k,v in totals.items()},'total_cycles_per_frame':sum(totals.values())/frames,'pal_frame_percent':sum(totals.values())/frames/1600,'ms_at_8mhz':sum(totals.values())/frames/8000}
    rdb.cmd('profile 0',wait=.04);rdb.cmd('run',wait=.04);assert p.val('gBobsCompleted')==2;assert p.data('gBobsIndices',16)==before
    results.append(item);print(item,flush=True)
 rdb.s.close()
 # Normal main-loop cadence, measured independently of the synthetic batches.
 p.put('gBobsHold',0)
 cadence=[]
 for count in (4,8):
  h.tap('2'if count==4 else'3',hold=.05,after=.15)
  for backend in (0,1):
   if p.val('gBobsBlitter')!=backend:h.tap('B',hold=.05,after=.15)
   for trail in (0,1):
    if p.val('gBobsTrails')!=trail:h.tap('T',hold=.05,after=.15)
    h.tap('C',hold=.05,after=.15);f0=p.val('gBobsFrames',4);m0=p.val('gBobsMissedVbl',4);h.wait(.8);f=p.val('gBobsFrames',4)-f0;m=p.val('gBobsMissedVbl',4)-m0
    cadence.append({'backend':'blitter'if backend else'cpu','mode':'trails'if trail else'restore','bobs':count,'frames':f,'missed_vbls':m,'fps':50*f/(f+m)})
    if backend and count==4:
     h.tap('SPACE',hold=.05,after=.15);p.put('gBobsHold',1);h.wait(.1);p.preview(p.pages()[0],f'preview-{"trails"if trail else"restore"}.png');p.put('gBobsHold',0);h.tap('SPACE',hold=.05,after=.1)
 h.control('hatari-event keydown 01');h.wait(.1);h.control('hatari-event keyup 01');h.wait(.15);assert p.val('gBobsExited')==1
 report={'machine':'STE 68000 8 MHz, 4 MiB, PAL RGB, German TOS 1.62','scope':'Bobs ASM frame, GodLib sprite drawing, chunk restore/store; BLiTTER HOG stalls included. Excludes scene/reset, input, C Target dispatch, Screen_Update/VBL/OS.','path':'NOEUD, one complete 360-position cycle per case','profiles':results,'normal_cadence':cadence,'release_sha256':hashlib.sha256((APP/'DCKBOBS.PRG').read_bytes()).hexdigest(),'debug_sha256':hashlib.sha256(DEBUG.read_bytes()).hexdigest(),'godlib_archive_sha256':hashlib.sha256((APP.parents[1]/'godlib/libgod.a').read_bytes()).hexdigest()}
 (APP/'profiling.json').write_text(json.dumps(report,indent=2)+'\n');print('Cadence',cadence,flush=True)
