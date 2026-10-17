"""Verify the meter's real palette timing AND visible screenshot pixels."""
from pathlib import Path
import json,os,re,subprocess,sys,time
from PIL import Image
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
sys.path.insert(0,str(Path.home()/'.agents/skills/hatari-debugging/scripts'))
from hatari_session import HatariSession
root=Path(__file__).resolve().parents[1]
configs=[('st','2.06','TOS v2.06 (1991)(Atari Corp)(Mega-STE)(UK).img'),('ste','2.06','TOS v2.06 (1991)(Atari Corp)(Mega-STE)(UK).img'),('ste','1.62','TOS v1.62 (1990)(Atari Corp)(STE)(GB)[STE TOS, Rev 2].img')]
if len(sys.argv)>1:configs=[c for c in configs if c[0]+'-'+c[1]==sys.argv[1]]
results=[]
for machine,version,rom in configs:
 tag=machine+'-'+version;trace=root/('analysis/meter-'+tag+'.log')
 with HatariSession(str(root/'SCROLL8.PRG'),machine=machine,screenshot_dir=str(root/'analysis/shots/meter'/tag/str(int(time.time()))),debug_except='bus,address,illegal',extra_args=['--spec512','1','--tos',str(Path.home()/'Atari/tos'/rom),'--confirm-quit','false','--memsize','1','--cpuclock','8','--cpulevel','0','--monitor','rgb','--trace','video_color','--trace-file',str(trace)]) as h:
  h.wait(8);h.tap('R');checks=[]
  for key,mode,colours in [('1','mcoder',[0x70,1]),('2','griff',[0x750,1]),('3','both',[0x70,0x750,1]),('SPACE','paused',[0x333,1]),('R','off',[])]:
   h.tap(key);h.wait(.25);start=len(trace.read_bytes());h.wait(.25);shot=h.screenshot();lines=trace.read_text()[start:]
   events=[]
   for l in lines.splitlines():
    m=re.search(r'write col addr=ff8240 col=(\w+) video_cyc_w=(\d+) line_cyc_w=(\d+).*video_hbl_w=(\d+)',l)
    if m:events.append({'colour':int(m[1],16),'cycle':int(m[2]),'line':int(m[4])})
   segments=[]
   if colours:
    i=0
    while i+len(colours)<=len(events):
     e=events[i:i+len(colours)]
     if [v['colour'] for v in e]!=colours:i+=1;continue
     assert 94<=e[0]['line']<=104,(tag,mode,e)
     assert all(63<=v['line']<263 for v in e),(tag,mode,e)
     durations=[e[j+1]['cycle']-e[j]['cycle'] for j in range(len(e)-1)]
     assert all(2500<=v<=12000 for v in durations),(mode,durations)
     segments.append({'lines':[v['line'] for v in e],'cycles':durations});i+=len(colours)
    assert len(segments)>=10,(tag,mode,len(segments),events[:9])
   else:assert not events,(tag,'off still writes palette',events[:5])
   im=Image.open(shot).convert('RGB').crop((0,108,832,218));pixels=list(im.get_flattened_data())
   green=sum(g>150 and r<50 and b<50 for r,g,b in pixels)
   orange=sum(r>140 and 50<g<230 and b<50 for r,g,b in pixels)
   grey=sum(30<r<230 and r==g==b for r,g,b in pixels)
   assert (green>500)==(mode in ['mcoder','both']),(tag,mode,green)
   assert (orange>500)==(mode in ['griff','both']),(tag,mode,orange)
   if mode=='paused':assert grey>500,(tag,grey)
   checks.append({'mode':mode,'verified_frames':len(segments),'green_pixels':green,'orange_pixels':orange,'grey_pixels':grey,'sample_segments':segments[:3],'screenshot':shot})
   print(tag,'PASS visible meter',mode,'frames',len(segments),flush=True)
  h.control('hatari-event keydown 01');h.wait(.3);h.control('hatari-event keyup 01');h.wait(4)
  assert not any(any(e in l for e in ['Bus Error','Address Error','Illegal instruction']) for l in h.lines)
 result={'machine':machine,'tos':version,'visible_timing_and_screenshots':True,'checks':checks}
 results.append(result)
 (root/('analysis/meter-results-'+tag+'.json')).write_text(json.dumps(result,indent=2)+'\n')
print('PASS',len(results),'configurations',flush=True)
