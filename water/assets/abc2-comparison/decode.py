"""Show actual exported STF/STE palettes and Atari bitplanes, not RGB444 reviews."""
from pathlib import Path
from PIL import Image
import json,struct
r=Path(__file__).resolve().parent
results=[]
for name in ('plain','floyd','ste-plain','ste-floyd'):
 raw=(r/name/'castle.gfx').read_bytes();pal=(r/name/'castle.pal').read_bytes()
 assert len(raw)==32000 and len(pal)==32
 ste=name.startswith('ste-')
 words=struct.unpack('>16H',pal);assert all((w&~(0xfff if ste else 0x777))==0 for w in words)
 def component(n):
  return (((n&7)<<1)|(n>>3))*17 if ste else round((n&7)*255/7)
 rgb=[tuple(component((w>>s)&15) for s in (8,4,0)) for w in words]
 pixels=[]
 for y in range(200):
  for x in range(20):
   planes=struct.unpack_from('>4H',raw,y*160+x*8)
   pixels.extend(rgb[sum(((planes[p]>>(15-i))&1)<<p for p in range(4))] for i in range(16))
 im=Image.new('RGB',(320,200));im.putdata(pixels)
 count=len(im.getcolors(64000));assert count<=16
 if ste:assert im.tobytes()==Image.open(r/name/'tool-preview.png').convert('RGB').tobytes()
 im.save(r/('castle-'+name+'.png'))
 im.resize((640,400),Image.Resampling.NEAREST).save(r/('castle-'+name+'-2x.png'))
 (r/('CASTLE-'+name.upper()+'.PI1')).write_bytes(b'\0\0'+pal+raw)
 results.append({'variant':name,'size':[320,200],'unique_colours':count,'palette_hardware_words':[hex(w) for w in words],'hardware':('STE 4096-colour gamut' if ste else 'STF 512-colour gamut')+', single global palette','shown_output':'Decoded exported castle.gfx and castle.pal; RGB preview is not used','dithering_stage':('RGB888 to '+('RGB444' if ste else 'RGB333')+' before greedy 16-colour palette fitting') if name.endswith('floyd') else 'none'})
(r/'results.json').write_text(json.dumps(results,indent=2)+'\n');print(json.dumps(results,indent=2))
