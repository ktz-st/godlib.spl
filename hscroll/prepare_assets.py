"""ABC2: 640x200 panorama, one 16-colour STE palette, no dithering."""
from pathlib import Path
import sys
from PIL import Image
root=Path(__file__).resolve().parent
sys.path.insert(0,str(root.parent/'tools'))
from abc2_assets import save
image=Image.open(root/'assets/panorama-original.png').convert('RGB').resize((640,200),Image.Resampling.LANCZOS)
save(image,root/'PANORAMA.BIN',root/'assets/panorama-st.png',locks={15:0xfff},header=False)
print('PANORAMA.BIN: ABC2, 640x200, 16 STE colours, no dithering; pixels verified')
