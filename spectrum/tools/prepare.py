"""SPU asset split and reference RGB render. No runtime conversion is required."""
from pathlib import Path
import struct,json
from PIL import Image
r=Path(__file__).resolve().parents[1];b=(r/'assets/PICTURE.SPU').read_bytes();assert len(b)==51104
pal=struct.unpack('>9552H',b[32000:]);st=[v&0x777 for v in pal]
(r/'assets/PIXELS.BIN').write_bytes(bytes(160)+b[160:32000])
(r/'assets/PALSTE.BIN').write_bytes(b[32000:])
(r/'assets/PALST.BIN').write_bytes(struct.pack('>9552H',*st))
for name,table,ste in [('reference-st.png',st,False),('reference-ste.png',pal,True)]:
 im=Image.new('RGB',(320,200));pix=im.load()
 for y in range(1,200):
  for x in range(320):
   off=y*160+(x//16)*8;words=struct.unpack_from('>4H',b,off);bit=15-(x&15)
   c=sum(((v>>bit)&1)<<p for p,v in enumerate(words))
   threshold=10*c+(-5 if c&1 else 1)
   idx=c+(32 if x>=threshold+160 else 16 if x>=threshold else 0)
   v=table[(y-1)*48+idx]
   rgb=[]
   for shift in (8,4,0):
    n=(v>>shift)&15;q=((n&7)*2+(n>>3)) if ste else n&7
    rgb.append(q*17 if ste else q*34)
   pix[x,y]=tuple(rgb)
 im.save(r/'assets'/name)
(r/'assets/stats.json').write_text(json.dumps({'source':'stsys10/spec512/pic.spu','palette_words':len(pal),'distinct_ste_palette_words':len(set(pal)),'distinct_st_palette_words':len(set(st))},indent=2)+'\n')
