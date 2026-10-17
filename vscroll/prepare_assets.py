"""ABC2: 320x400 tower, one 16-colour STE palette, no dithering."""
from pathlib import Path
import sys
from PIL import Image
root=Path(__file__).resolve().parent
sys.path.insert(0,str(root.parent/'tools'))
from abc2_assets import save
image=Image.open(root/'assets/tower-original.png').convert('RGB').resize((320,400),Image.Resampling.LANCZOS)
save(image,root/'TOWER.BIN',root/'assets/tower-st.png',locks={15:0xfff},header=False)
print('TOWER.BIN: ABC2, 320x400, 16 STE colours, no dithering; pixels verified')
