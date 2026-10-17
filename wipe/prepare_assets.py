"""ABC2 RGB artwork -> individual-palette STE PI1 files, no dithering."""
from pathlib import Path
import sys
from PIL import Image
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent/'tools'))
from abc2_assets import save
for name in (sys.argv[1:] or ('coast','space','forest')):
    image=Image.open(ROOT/'assets'/f'{name}.png').convert('RGB').resize((320,200),Image.Resampling.LANCZOS)
    save(image,ROOT/f'{name.upper()}.PI1',ROOT/'assets'/f'{name}-st.png',locks={15:0xfff})
    print(f'{name.upper()}.PI1: ABC2, 16 STE colours, no dithering; black 0 / white 15 retained')
