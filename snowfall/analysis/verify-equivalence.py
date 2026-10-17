"""Run original and optimized kernels on identical evolving planar screens."""
from pathlib import Path
import json,os,struct,subprocess,sys,time
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
sys.path.insert(0,str(Path.home()/'.codex/skills/hatari-debugging/scripts'))
from hatari_session import HatariSession
root=Path(__file__).resolve().parents[1];exe=root/'analysis/SVER.PRG'
s={p[2]:int(p[0],16) for l in subprocess.check_output(['m68k-atari-mintelf-nm',str(exe)],text=True).splitlines() if len(p:=l.split())==3}
rom='/Users/kriss/Atari/tos/TOS v2.06 (1991)(Atari Corp)(Mega-STE)(UK).img'
with HatariSession(str(exe),machine='st',extra_args=['--tos',rom,'--confirm-quit','false','--memsize','1','--cpuclock','8','--monitor','rgb','--fast-forward','true'],debug_except='bus,address,illegal') as h:
 h.wait(8);base=h.basepage()['text']
 def count(n):
  a=base+s[n];return h.mem(a,4).u32(a)
 for _ in range(40):
  checks=count('gSnowChecks');mismatch=count('gSnowMismatch')
  print('checks',checks,'mismatches',mismatch,flush=True)
  assert mismatch==0
  if checks==1200:break
  h.wait(3)
 assert checks==1200
 (root/'analysis/equivalence.json').write_text(json.dumps({'steps':checks,'mismatches':mismatch,'same_input_both_kernels':True,'scenarios':['sparse flakes','dense flakes','new platform','erased platform gap','wide platform and piles']},indent=2)+'\n')
