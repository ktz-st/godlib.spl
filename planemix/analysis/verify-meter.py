"""Verify real green timing pixels, marker-off state and palette restoration."""
from pathlib import Path
from PIL import Image
import os,sys,subprocess,json
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
sys.path.insert(0,str(Path.home()/'.agents/skills/hatari-debugging/scripts'))
from hatari_session import HatariSession
root=Path(__file__).resolve().parents[1]
sym={p[2]:int(p[0],16) for l in subprocess.check_output(['m68k-atari-mintelf-nm',str(root/'analysis/LAYDB.PRG')],text=True).splitlines() if len(p:=l.split())==3}
rom=Path.home()/'Atari/tos/TOS v2.06 (1991)(Atari Corp)(Mega-STE)(UK).img'
with HatariSession(str(root/'LAYFX.PRG'),machine='st',sound=False,screenshot_dir=str(root/'analysis/shots/meter'),debug_except='bus,address,illegal',extra_args=['--spec512','1','--tos',str(rom),'--confirm-quit','false','--memsize','1','--cpuclock','8','--monitor','rgb']) as h:
 h.wait(8);base=h.basepage()['text'];h.tap('R');h.wait(.3);on=h.screenshot()
 def green(p):return sum(g>200 and r<20 and b<20 for r,g,b in Image.open(p).convert('RGB').get_flattened_data())
 oncount=green(on);assert oncount>500,oncount
 h.debug('b pc = $%x :once'%(base+sym['Screen_Update']))
 restored=h.mem(0xffff8240,2,paused=True).u16(0xffff8240)&0x777;assert restored==1,hex(restored)
 h.stdin_cmd('c');h.tap('R');h.wait(.3);off=h.screenshot();offcount=green(off);assert offcount==0,offcount
 h.control('hatari-event keydown 01');h.wait(.2);h.control('hatari-event keyup 01');h.wait(3)
 assert h.mem(base+sym['gFxExited'],2).u16(base+sym['gFxExited'])==1
 assert not any(any(e in l for e in ['Bus Error','Address Error','Illegal instruction']) for l in h.lines)
 result={'machine':'st','tos':'2.06','green_pixels_on':oncount,'green_pixels_off':offcount,'restored_colour_zero':restored,'on_screenshot':on,'off_screenshot':off,'clean_exit':True}
 (root/'analysis/meter-results.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS visible CPU band and restored palette',result,flush=True)
