"""Decode the actual 4-plane PI1 outputs; previews therefore have <=16 colours.
Mask off STE extra colour bits so these deliverables use the original ST gamut.
No pixel remapping, extra dithering or palette fitting is performed here.
"""
from pathlib import Path
from PIL import Image
import struct,json
r=Path(__file__).resolve().parent
results=[]
for name in ('plain','dither'):
 p=r/name/'pic_f0.pi1'
 if not p.exists():continue
 b=p.read_bytes();assert len(b)==32034 and b[:2]==b'\0\0'
 words=[w&0x777 for w in struct.unpack('>16H',b[2:34])]
 palette=[tuple(round(((w>>s)&7)*255/7) for s in (8,4,0)) for w in words]
 indices=[]
 for y in range(200):
  for x in range(0,320,16):
   planes=struct.unpack_from('>4H',b,34+y*160+(x//16)*8)
   indices.extend(sum(((planes[p]>>(15-i))&1)<<p for p in range(4)) for i in range(16))
 im=Image.new('RGB',(320,200));im.putdata([palette[i] for i in indices])
 colours=len(im.getcolors(64000));assert colours<=16
 im.save(r/('castle-'+name+'.png'))
 im.resize((640,400),Image.Resampling.NEAREST).save(r/('castle-'+name+'-2x.png'))
 (r/('CASTLE-'+name.upper()+'.PI1')).write_bytes(struct.pack('>17H',0,*words)+b[34:])
 results.append({'variant':name,'unique_colours':colours,'palette_st_words':[hex(w) for w in words],'source':'Original RGB castle resized to 320x200, not previously reduced art','native_tool':'PhotoChrome/CryptoChrome v6.44, -cd st -pc 4 -ccmode 1','ccfields':1 if name=='plain' else 2,'shown_output':'pic_f0.pi1, one actual four-plane static field','pixel_data_unchanged':True})
(r/'results.json').write_text(json.dumps(results,indent=2)+'\n')
print(json.dumps(results,indent=2))
