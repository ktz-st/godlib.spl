"""Rebuild generated scene artwork with ABC2 STE/no dithering and its examples."""
from pathlib import Path
import subprocess,sys
root=Path(__file__).resolve().parents[1]
for sample,script in [('wipe','prepare_assets.py'),('hscroll','prepare_assets.py'),
 ('vscroll','prepare_assets.py'),('water','tools/prepare.py'),('snowfall','tools/prepare.py')]:
    subprocess.run([sys.executable,script],cwd=root/sample,check=True)
for sample in ('wipe','hscroll','vscroll','palsplit','splitscreen','splitscreenh',
               'wobble','water','reflect','snowfall','flagwave'):
    subprocess.run(['make','-C',str(root/sample),'debug'],check=True)
