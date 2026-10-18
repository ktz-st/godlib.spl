"""Full native-frame oracle from SuperHex's half-plane equations and clipped edges."""
import os,sys,struct,time,json,math,hashlib
from pathlib import Path
from PIL import Image
os.environ.setdefault('SDL_VIDEODRIVER','dummy');os.environ.setdefault('SDL_AUDIODRIVER','dummy')
sys.path.insert(0,str(Path.home()/'.agents/skills/hatari-debugging/scripts'))
from hatari_session import HatariSession,nm_symbols
root=Path(__file__).resolve().parents[1];out=root/'analysis'
sym=nm_symbols(str(out/'IRISDBG.PRG'),nm='m68k-atari-mintelf-nm')
sine=[max(-16384,min(16383,round(math.sin(2*math.pi*i/1536)*16384)))for i in range(1920)]
def div(a,b):return (abs(a)//abs(b))*(-1 if (a<0)!=(b<0)else 1)
def spans(h,a):
 edges=[]
 for k in range(6):
  t=(a+k*256+128)%1536;c=sine[t+384];sn=sine[t];rhs=h*16384
  edges.append([0 if c>0 else 1,div(rhs+100*sn,c)*16,-div(sn*16,c)]if abs(c)>256 else[2,sn,100+div(rhs,sn)])
 result=[]
 for y in range(200):
  lo=-100000;hi=100000;ok=h>2
  for e in edges:
   if e[0]==0:hi=min(hi,e[1]);e[1]+=e[2]
   elif e[0]==1:lo=max(lo,e[1]);e[1]+=e[2]
   elif y>e[2]if e[1]>0 else y<e[2]:ok=False
  l=max(0,160+(lo>>4));r=min(319,160+(hi>>4));result.append((l,r)if ok and l<=r else(1,0))
 return result

def code(x,y):return (1 if x<0 else 2 if x>319 else 0)|(4 if y<0 else 8 if y>199 else 0)
def line(x0,y0,x1,y1):
 while True:
  c0=code(x0,y0);c1=code(x1,y1)
  if not(c0|c1):break
  if c0&c1:return
  c=c0 or c1
  if c&8:x=x0+div((x1-x0)*(199-y0),y1-y0);y=199
  elif c&4:x=x0+div((x1-x0)*(-y0),y1-y0);y=0
  elif c&2:y=y0+div((y1-y0)*(319-x0),x1-x0);x=319
  else:y=y0+div((y1-y0)*(-x0),x1-x0);x=0
  if c==c0:x0,y0=x,y
  else:x1,y1=x,y
 dx=abs(x1-x0);dy=-abs(y1-y0);sx=1 if x1>=x0 else -1;sy=1 if y1>=y0 else -1;err=dx+dy
 while True:
  yield x0,y0
  if x0==x1 and y0==y1:return
  e2=2*err
  if e2>=dy:err+=dy;x0+=sx
  if e2<=dx:err+=dx;y0+=sy

def oracle(source,h,a):
 data=bytearray(source)
 if h<=2:return data
 for y,(l,r)in enumerate(spans(h,a)):
  if l>r:continue
  for w in range(l//16,r//16+1):
   bits=(65535>>(l%16)if w==l//16 else 65535)&((65535<<(15-r%16))&65535 if w==r//16 else 65535)
   struct.pack_into('>H',data,y*160+w*8+6,bits)
 radius=h*37837>>15
 xy=[(160+(radius*sine[(a+k*256)%1536+384]>>14),100+(radius*sine[(a+k*256)%1536]>>14))for k in range(7)]
 for k in range(6):
  for x,y in line(*xy[k],*xy[k+1]):
   at=y*160+(x//16)*8+(x%16)//8;mask=1<<(7-x%8)
   for p in range(4):data[at+2*p]|=mask
 return data

def image(data,palette):
 from PIL import Image
 words=struct.unpack('>16H',palette);rgb=[tuple(((((v>>s)&7)<<1)|(((v>>s)>>3)&1))*17 for s in(8,4,0))for v in words];pix=[]
 for y in range(200):
  for w in range(20):
   planes=struct.unpack_from('>4H',data,y*160+w*8)
   pix.extend(rgb[sum(((p>>(15-i))&1)<<j for j,p in enumerate(planes))]for i in range(16))
 im=Image.new('RGB',(320,200));im.putdata(pix);return im
results=[];previews=[]
for machine,cycles in [('ste',2),('st',1)]:
 tos='TOS v1.62 (1990)(Atari Corp)(STE)(De).img'if machine=='ste'else 'TOS v2.06 (1991)(Atari Corp)(Mega-STE)(UK).img'
 with HatariSession(str(root/'IRIS.PRG'),tos=str(Path.home()/'Atari/tos'/tos),machine=machine,sound=False,screenshot_dir=str(out/'shots'),debug_except='bus,address,illegal',extra_args=['--confirm-quit','false','--memsize','1','--cpuclock','8','--monitor','rgb']) as h:
  h.wait(9);base=h.basepage()['text'];a=lambda n:base+sym[n]
  def stop():h.debug('b pc = $%x :once'%a('Iris_FrameDone'),settle=.2)
  def step():h.stdin_cmd('b pc = $%x :once'%a('Iris_FrameDone'),settle=.005);h.stdin_cmd('c',settle=.08)
  def dump(addr,n):
   f=out/'dump.bin';f.unlink(missing_ok=True);h.stdin_cmd('savebin %s $%x $%x'%(f,addr,n),settle=.008)
   for _ in range(200):
    if f.exists()and f.stat().st_size==n:break
    time.sleep(.005)
   data=f.read_bytes();assert len(data)==n;return data
  def u16(n):return struct.unpack('>H',dump(a(n),2))[0]
  def pointer(n):return struct.unpack('>I',dump(a(n),4))[0]
  names=['gIrisDrawStage','gIrisDrawStep','gIrisDrawPicture','gIrisDrawAngle','gIrisDrawH','gIrisScreen'];lo=min(a(n)for n in names);hi=max(a(n)+(4 if n=='gIrisScreen'else 2)for n in names)
  def state():
   data=dump(lo,hi-lo);return {n:struct.unpack_from('>I'if n=='gIrisScreen'else '>H',data,a(n)-lo)[0]for n in names}
  def key(k):h.control('hatari-event keydown '+k);step();h.control('hatari-event keyup '+k)
  stop();assert u16('gIrisReady')==1 and u16('gIrisStage')==0
  assert u16('gIrisHasBlitter')==(machine=='ste')
  sources={0:dump(pointer('gIrisBackground'),32000)}
  pages=set();displayed={};checks=0
  for cycle in range(cycles):
   key('49');seen=False;stages=set();steps=set()
   for frame in range(90):
    s=state();mode=s['gIrisDrawStage'];pic=s['gIrisDrawPicture'];tick=s['gIrisDrawStep'];angle=s['gIrisDrawAngle'];height=s['gIrisDrawH'];screen=s['gIrisScreen']
    if pic not in sources:sources[pic]=dump(pointer('gIrisBackground'),32000)
    assert 0<=pointer('gIrisLogEnd')-pointer('gIrisLogBase')<=3072
    actual=dump(screen,32000);expected=oracle(sources[pic],height,angle)if mode else sources[pic]
    # During the closed shutter, planes 0..2 change in 50-row strips.
    # Raw hidden image bits may differ, but every displayed pixel must match.
    progress=struct.unpack('>2H',dump(a('gIrisCopyRow'),4))
    pending=any(row<200 for row in progress)
    if actual!=expected and pending:
     assert all(actual[pos:pos+2]==b'\xff\xff' for pos in range(6,32000,8)),('copy exposed',s,progress)
     palette=(root/('assets/PALETTE2.BIN'if pic else 'assets/PALETTE.BIN')).read_bytes()
     assert image(actual,palette).tobytes()==image(expected,palette).tobytes(),('visible copy difference',s,progress)
     expected=actual
    if actual!=expected:
     (out/'actual.bin').write_bytes(actual);(out/'expected.bin').write_bytes(expected)
     raise AssertionError((machine,cycle,s,next((i,x,y)for i,(x,y)in enumerate(zip(actual,expected))if x!=y)))
    pal=(root/('assets/PALETTE2.BIN'if pic else 'assets/PALETTE.BIN')).read_bytes()
    displayed[screen]=(actual,pal);pages.add(screen);checks+=1
    vid=dump(0xffff8200,14);phys=(vid[1]<<16)|(vid[3]<<8)|(vid[13]if machine=='ste'else 0)
    if phys in displayed and any(displayed[phys][0]):
     livepal=dump(0xffff8240,32)
     if machine=='st':
      livepal=struct.pack('>16H',*(v&0x777 for v in struct.unpack('>16H',livepal)))
      old,palwas=displayed[phys];displayed[phys]=(old,struct.pack('>16H',*(v&0x777 for v in struct.unpack('>16H',palwas))))
     if livepal!=displayed[phys][1]:
      assert image(displayed[phys][0],livepal).tobytes()==image(*displayed[phys]).tobytes(),('physical palette mismatch',machine,s)
    if mode:
     seen=True;stages.add(mode);steps.add((mode,tick))
     if machine=='ste'and cycle==0 and mode==1 and tick in(8,16,24,32,40):previews.append(image(actual,pal))
    if seen and mode==0:break
    step()
   else:raise AssertionError('Transition timeout')
   assert stages=={1,2} and all((m,t)in steps for m in(1,2)for t in range(41)),steps
   print('PASS native',machine,'cycle',cycle+1,'frames',checks,flush=True)
  # Pause must leave the same rendered frame on BOTH pages.
  key('49');step();key('25')
  for _ in range(5):
   if u16('gIrisPause')==1:break
   step()
  assert u16('gIrisPause')==1
  step()
  frozen=state();data=dump(frozen['gIrisScreen'],32000)
  for _ in range(3):
   step();now=state();assert now['gIrisDrawAngle']==frozen['gIrisDrawAngle']and now['gIrisDrawStep']==frozen['gIrisDrawStep'];assert dump(now['gIrisScreen'],32000)==data
  key('25')
  h.stdin_cmd('c',settle=.1);h.tap('ESC',hold=.15,after=.6)
  assert h.mem(a('gIrisExited'),2).u16(a('gIrisExited'))==1
  assert not any(any(s in l for s in ['Bus Error','Address Error','Illegal instruction'])for l in h.lines)
  assert len(pages)==2
  results.append({'machine':machine,'TOS':tos,'cycles':cycles,'full_frame_comparisons':checks,'pages':len(pages),'pause_both_pages':True,'exit':True})
if previews:
 sheet=Image.new('RGB',(320*len(previews),200))
 for i,im in enumerate(previews):sheet.paste(im,(i*320,0))
 sheet.save(out/'preview.png')
(out/'verification.json').write_text(json.dumps({'program_sha256':hashlib.sha256((root/'IRIS.PRG').read_bytes()).hexdigest(),'TOS':'STE: German 1.62; ST: UK 2.06 (1.62 is STE-only)','configuration':'68000, 8 MHz, 1 MiB, RGB PAL','checks':'Complete VRAM vs independent SuperHex half-plane/edge oracle; all 41 steps in each direction, two pages, palette synchronized with physical page, 7-colour sources and independent plane-3 mask, pause, exit. CPU ASM on both ST and STE: differential plane-3 spans, sparse reverse undo of white word groups. Hidden 50-row image strips are checked by displayed colours under a fully set mask; remaining frames compare all VRAM bytes.','results':results},indent=2)+'\n')
(out/'dump.bin').unlink(missing_ok=True)
print('PASS all native iris tests',results,flush=True)
