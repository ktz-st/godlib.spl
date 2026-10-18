"""Native TV transitions: independent complete-frame oracle, both image palettes/pages."""
import os,sys,struct,time,json,hashlib,shutil
from pathlib import Path
os.environ.setdefault('SDL_VIDEODRIVER','dummy');os.environ.setdefault('SDL_AUDIODRIVER','dummy')
sys.path.insert(0,str(Path.home()/'.agents/skills/hatari-debugging/scripts'))
from hatari_session import HatariSession,nm_symbols
root=Path(__file__).resolve().parents[1]
sym=nm_symbols(str(root/'analysis/CRTDBG.PRG'),nm='m68k-atari-mintelf-nm')
shapes=json.loads((root/'assets/tvsteps.json').read_text());ref=json.loads((root/'assets/tvpalettes.json').read_text());results=[];palettes=set();pages=set();displayed={}
with HatariSession(str(root/'CRT.PRG'),tos=str(Path.home()/'Atari/tos/TOS v1.62 (1990)(Atari Corp)(STE)(De).img'),machine='ste',sound=False,screenshot_dir=str(root/'analysis/shots'),debug_except='bus,address,illegal',extra_args=['--confirm-quit','false','--memsize','1','--cpuclock','8','--monitor','rgb']) as h:
 h.wait(9);base=h.basepage()['text'];a=lambda n:base+sym[n]
 def stop():h.debug('b pc = $%x :once'%a('Crt_FrameDone'),settle=.12)
 def step():h.stdin_cmd('b pc = $%x :once'%a('Crt_FrameDone'),settle=.01);h.stdin_cmd('c',settle=.05)
 def dump(addr,n):
  f=root/'analysis/tv-dump.bin';f.unlink(missing_ok=True);h.stdin_cmd('savebin %s $%x $%x'%(f,addr,n),settle=.01)
  for _ in range(200):
   if f.exists()and f.stat().st_size==n:break
   time.sleep(.005)
  data=f.read_bytes();assert len(data)==n;return data
 def write(addr,data):h.stdin_cmd('w $%x '%addr+' '.join('$%02x'%v for v in data),settle=.01)
 def u16(n):return struct.unpack('>H',dump(a(n),2))[0]
 def ptr(n):return struct.unpack('>I',dump(a(n),4))[0]
 stop();assert u16('gCrtReady')==1 and u16('gCrtTvMode')==0
 write(a('gCrtAuto'),b'\0\0')
 sources={0:dump(ptr('gCrtTvSource'),32000)}
 for cycle in range(2):
  assert u16('gCrtTvMode')==0
  # Actual IKBD input, not a forced state transition.
  h.control('hatari-event keydown 49');step();h.control('hatari-event keyup 49')
  seen=False;counts={};lastpal=dump(0xffff8240,32)
  for frame in range(220):
   mode=u16('gCrtTvDrawMode');idx=u16('gCrtTvDrawStep');pic=u16('gCrtTvDrawPicture')
   if mode:
    seen=True;w,hh=shapes[idx];out=bytearray(32000)
    if pic not in sources:sources[pic]=dump(ptr('gCrtTvSource'),32000)
    source=sources[pic]
    if idx>=ref['image_start']:
     for y in range(hh):
      sy=100+int((y-hh//2)*200/hh)
      out[((200-hh)//2+y)*160:((200-hh)//2+y+1)*160]=source[sy*160:(sy+1)*160]
    elif hh:
     for y in range(hh):
      span=w;colour=1 if hh==4 and y in (0,3) else 7
      for x in range((320-span)//2,(320+span)//2):
       at=((200-hh)//2+y)*160+(x//16)*8
       for plane in range(3):
        if colour&(1<<plane):out[at+plane*2+(x%16)//8]|=1<<(7-x%8)
    screen=ptr('gCrtScreen');actual=dump(screen,32000)
    if actual!=out:
     (root/'analysis/tv-actual.bin').write_bytes(actual);(root/'analysis/tv-expected.bin').write_bytes(out)
     raise AssertionError({'cycle':cycle,'frame':frame,'mode':mode,'step':idx,'shape':[w,hh],'firstdiff':next((i,x,y)for i,(x,y)in enumerate(zip(actual,out))if x!=y)})
    displayed[screen]=(pic,idx,bytes(out));pages.add(screen);counts[(mode,idx)]=counts.get((mode,idx),0)+1
    results.append({'cycle':cycle,'mode':mode,'step':idx,'picture':pic,'page':screen})
   pal=dump(0xffff8240,32)
   # Check the physical page's palette, not the newly drawn Logic page.
   vid=dump(0xffff8200,14);phys=(vid[1]<<16)|(vid[3]<<8)|vid[13]
   if phys in displayed:
    pp,ss,pixels=displayed[phys]
    wanted=struct.pack('>16H',*ref['palettes'][pp][ss])
    if pixels!=bytes(32000):assert pal==wanted,('displayed palette mismatch',mode,idx,pp,ss,pal.hex(),wanted.hex())
   words=struct.unpack('>16H',pal);assert words[0]==0 and words[8]==0,'background brightened'
   lastpal=pal
   if seen and u16('gCrtTvMode')==0:
    step();break
   step()
  else:raise AssertionError('transition timed out')
  assert all(counts.get((mode,i),0)>=2 for mode in (1,2)for i in range(len(shapes))),counts
  suffix='' if u16('gCrtPicture')==0 else '2'
  assert dump(0xffff8240,32)==(root/('assets/PALETTE'+suffix+'.BIN')).read_bytes()
  palettes.add(suffix)
  # Also validate the first normal renderer frame after each new picture:
  # catches stale page histories or a source pointer left on the old asset.
  raw=(root/('assets/INDICES'+suffix+'.BIN')).read_bytes()
  expected=bytearray(sources[u16('gCrtPicture')])
  shifts=struct.unpack('>11h',dump(a('gCrtX'),22));dy=struct.unpack('>h',dump(a('gCrtY'),2))[0]
  band=struct.unpack('>h',dump(a('gCrtBand'),2))[0];scan=u16('gCrtScan')
  for y in range(16,192):
   line=raw[(y-dy)*320:(y-dy+1)*320];dx=shifts[(y-16)//16]
   line=bytes(dx)+line[:320-dx]if dx>=0 else line[-dx:]+bytes(-dx)
   mask=bool(scan and y&1 and not band<=y-16<band+22)
   for x in range(0,320,16):
    vals=line[x:x+16];words=[sum(((v>>pl)&1)<<(15-j)for j,v in enumerate(vals))for pl in range(3)]+[65535 if mask else 0]
    struct.pack_into('>4H',expected,y*160+x//16*8,*words)
  assert dump(ptr('gCrtScreen'),32000)==expected,'normal renderer source/history after scene switch'
  h.stdin_cmd('c',settle=.1);h.wait(.2)
  shot=h.screenshot();shutil.copy2(shot,root/('analysis/preview'+suffix+'.png'));stop()
 assert len(pages)==2 and len(palettes)==2
 h.stdin_cmd('c',settle=.1);h.control('hatari-event keydown 01');h.wait(.1);h.control('hatari-event keyup 01');h.wait(.4)
 assert h.mem(a('gCrtExited'),2).u16(a('gCrtExited'))==1
 faults=[l for l in h.lines if any(s in l for s in ['Bus Error','Address Error','Illegal instruction'])];assert not faults,faults
 (root/'analysis/tv-verification.json').write_text(json.dumps({'machine':'STE 8 MHz, 1 MiB, German TOS 1.62','program_sha256':hashlib.sha256((root/'CRT.PRG').read_bytes()).hexdigest(),'frames':len(results),'steps_per_direction':len(shapes),'pages':len(pages),'checks':'Two actual N-key cycles, both pictures/palettes, complete VRAM bytes at every off/on step on both pages, palette brightening synchronized to displayed page, black background preserved, scene swap on black, first normal frame source/history after each swap, clean exit','cases':results},indent=2)+'\n')
 (root/'analysis/tv-dump.bin').unlink(missing_ok=True)
 print('PASS',len(results),'TV full-frame comparisons, both pages, both pictures, synchronized brightening, thin fading line, normal source/history and exit')
