from common import *
import hashlib
results={'full_buffer_checks':0,'byte_mismatches':0,'cases':[]}
with HatariSession(str(DEBUG),hatari='/opt/homebrew/opt/hatari/Hatari.app/Contents/MacOS/hatari',tos=str(TOS),extra_args=['--confirm-quit','false','--memsize','4','--cpulevel','0','--cpuclock','8','--monitor','rgb','--fast-forward','true'])as h:
 p=Probe(h);assert p.val('gBobsCount')==4;p.put('gBobsHold',1);h.wait(.1)
 for backend in (0,1):
  for trail in (0,1):
   for path in range(8):
    for count in (1,4,8):
     p.put('gBobsBlitter',backend);p.put('gBobsTrails',trail);p.put('gBobsPath',path);p.put('gBobsCount',count);p.put('gBobsPaused',0);p.put('gBobsReset',1);p.request()
     pages=p.pages();back=p.raw(pages[2],32000);expected=[bytearray(back),bytearray(back)];idx=[i*12 for i in range(8)];cur=positions(path,idx)
     for page in expected:stamp(page,cur,count)
     for frame in range(3):
      if frame:p.request()
      previous=cur;idx=[(n+1)%len(PATHS[path])for n in idx];cur=positions(path,idx);page=frame&1
      if trail:stamp(expected[page],previous,count)
      else:expected[page]=bytearray(back)
      stamp(expected[page],cur,count)
      assert list(struct.unpack('>8H',p.data('gBobsIndices',16)))==[n*4 for n in idx]
      assert list(struct.iter_unpack('>hh',p.data('gBobsPositions',32)))==cur
      actual=p.raw(pages[page],32000);errors=sum(x!=y for x,y in zip(actual,expected[page]));assert not errors,(backend,trail,path,count,frame,errors)
      results['full_buffer_checks']+=1
     other=(frame&1)^1;assert p.raw(pages[other],32000)==expected[other];results['full_buffer_checks']+=1
     results['cases'].append({'backend':backend,'trails':trail,'path':path,'bobs':count})
    print('PASS',backend,trail,PATH_NAMES[path],flush=True)
 # All horizontal shifts and exact legal outer X positions, including overlap.
 for backend in (0,1):
  p.put('gBobsBlitter',backend);p.put('gBobsTrails',0);p.put('gBobsCount',8);p.put('gBobsReset',1);p.request();p.put('gBobsPaused',1);pages=p.pages();back=p.raw(pages[2],32000)
  for phase in list(range(16))+[0,288]:
   cur=[(phase if phase==288 else phase+16,40+i*10)for i in range(8)]
   p.write('gBobsPositions',b''.join(struct.pack('>hh',*v)for v in cur));page=p.val('gBobsTestPage');p.request();expected=bytearray(back);stamp(expected,cur,8);assert p.raw(pages[page],32000)==expected,(backend,phase);results['full_buffer_checks']+=1
 # Force each trajectory's wrap without traversing its full cycle in the debugger.
 p.put('gBobsPaused',0)
 for path in range(8):
  p.put('gBobsPath',path);p.put('gBobsReset',1);p.request();heads=[len(PATHS[path])-1]*8;p.write('gBobsIndices',b''.join(struct.pack('>H',n*4)for n in heads));p.request();assert p.data('gBobsIndices',16)==bytes(16);assert list(struct.iter_unpack('>hh',p.data('gBobsPositions',32)))==[PATHS[path][0]]*8
 results['all_16_shifts_and_overlap']=True;results['all_8_path_wraps']=True
 # Live controls, cadence and stable pause after leaving the deterministic hook.
 p.put('gBobsHold',0);h.tap('C',hold=.05,after=.15)
 for key,count in [('1',1),('2',4),('3',8)]:h.tap(key,hold=.05,after=.12);assert p.val('gBobsCount')==count
 old=p.val('gBobsTrails');h.tap('T',hold=.05,after=.12);assert p.val('gBobsTrails')==old^1
 h.tap('SPACE',hold=.05,after=.12);before=p.data('gBobsPositions',32);h.wait(.2);assert before==p.data('gBobsPositions',32);h.tap('SPACE',hold=.05,after=.12)
 for path in range(8):
  old=p.val('gBobsPath');h.tap('P',hold=.05,after=.12);assert p.val('gBobsPath')==(old+1)&7
 h.tap('P',hold=.05,after=.12);assert p.val('gBobsPath')==0
 for trail in (0,1):
  if p.val('gBobsTrails')!=trail:h.tap('T',hold=.05,after=.12)
  h.tap('C',hold=.05,after=.3);f0=p.val('gBobsFrames',4);m0=p.val('gBobsMissedVbl',4);h.wait(.6);f=p.val('gBobsFrames',4)-f0;m=p.val('gBobsMissedVbl',4)-m0;results['live_trails'if trail else'live_restore']={'frames':f,'missed_vbls':m,'fps':50*f/(f+m)}
  h.tap('SPACE',hold=.05,after=.1);p.put('gBobsHold',1);h.wait(.1);p.preview(p.pages()[p.val('gScreenClassPhysicIndex')if'gScreenClassPhysicIndex'in p.sy else 0],f'preview-{ "trails"if trail else"restore"}.png');p.put('gBobsHold',0);h.tap('SPACE',hold=.05,after=.1)
 h.control('hatari-event keydown 01');h.wait(.1);h.control('hatari-event keyup 01');h.wait(.2);assert p.val('gBobsExited')==1
 results['controls_and_exit']=True;results['machine']='STE 68000 8 MHz, 4 MiB, German TOS 1.62';results['release_sha256']=hashlib.sha256((APP/'DCKBOBS.PRG').read_bytes()).hexdigest();(APP/'verification.json').write_text(json.dumps(results,indent=2)+'\n');print(results['full_buffer_checks'],'full buffers passed',flush=True)
