from pathlib import Path
from PIL import Image
import struct

def make_preview():
 app=Path(__file__).resolve().parents[1]
 page=Image.open(app/'preview-0.png');assert page.mode=='P'
 data=(app/'assets/PALETTES.BIN').read_bytes();frames=[]
 for offset in range(0,len(data),32):
  rgb=[(((((w>>s)&7)<<1)|((w>>(s+3))&1))*17) for w in struct.unpack_from('>16H',data,offset) for s in (8,4,0)]
  im=page.copy();im.putpalette(rgb+[0]*(768-len(rgb)));frames.append(im.convert('RGB'))
 frames[0].save(app/'palette-cycle.gif',save_all=True,append_images=frames[1:],duration=40,loop=0)

if __name__=='__main__':make_preview()
