"""SuperHex bg_render: one 60-degree sector, 32 compact one-plane frames.
320x200 crop of original 320x246, CY=100, BG_CY=123 -> source row +23.
Generate the sine source and an offline mask oracle for verification.
The program builds the same cache in RAM once at startup, then copies in ASM.
"""
from pathlib import Path
import math,struct,json
root=Path(__file__).resolve().parent
sine=[max(-16384,min(16383,round(math.sin(2*math.pi*i/1536)*16384)))for i in range(1920)]
def div(a,b):return abs(a)//abs(b)*(-1 if(a<0)!=(b<0)else 1)
def signed(n):return (n+32768)%65536-32768
def frame(a):
 cot=[]
 for i in range(3):
  t=(a+i*256)%1536;c=sine[t+384];sn=sine[t]
  if -64<sn<64:sn=-64 if sn<0 else 64
  cot.append(signed(div(c*256,sn)))
 parity=((768-a)%1536>>8)&1
 out=bytearray(8000)
 for y in range(200):
  dy2=2*(y-100)+1;xs=sorted(max(-1000,min(1000,(320+(dy2*c>>8))>>1))for c in cot)
  left=-1000;p=parity
  for right in [v-1 for v in xs]+[1000]:
   l=max(0,left);r=min(319,right)
   if not p and l<=r:
    for w in range(l//16,r//16+1):
     mask=(65535>>(l%16)if w==l//16 else 65535)&((65535<<(15-r%16))&65535 if w==r//16 else 65535)
     at=y*40+2*w;old=struct.unpack_from('>H',out,at)[0];struct.pack_into('>H',out,at,old|mask)
   left=right+1;p^=1
 return bytes(out)
def live_cots():
 rows=[]
 for f in range(32):
  a=f*8+4;cot=[]
  for i in range(3):
   t=a+i*256;c=sine[t+384];sn=sine[t]
   if -64<sn<64:sn=-64 if sn<0 else 64
   cot.append(signed(div(c*256,sn)))
  ordered=sorted(cot)
  assert abs(ordered[1])*199<160*512  # median never leaves the viewport
  rows.append('        dc.w '+','.join(map(str,ordered)))
 (root/'assets/COTS.S').write_text('; Sorted Q8 cotangents for original 32 phase angles; 192 bytes.\n'+'\n'.join(rows)+'\n')
 (root/'assets/XMASKS.S').write_text('; x=0..320: tail mask, interleaved-word byte offset (1284 bytes).\n'+''.join('        dc.w $%04x,%d\n'%(65535>>(x%16),(x//16)*8)for x in range(321)))

def main():
 live_cots()
 (root/'assets/SINE.S').write_text('; Original SuperHex Q14 sine values.\n'+''.join('        dc.w '+','.join(map(str,sine[i:i+12]))+'\n'for i in range(0,len(sine),12)))
 frames=b''.join(frame(f*8+4)for f in range(32));(root/'assets/FRAMES.BIN').write_bytes(frames)
 (root/'assets/provenance.json').write_text(json.dumps({'source':'superhex_ste/src/main.c bg_render/bg_copy','frames':32,'frame_bytes':8000,'total_bytes':len(frames),'viewport':[320,200],'centre':[160,100],'angle_units_per_turn':1536,'sector_units':256,'frame_angle':'f*8+4','other_sectors':'invert on odd sectors','original_crop_row':23,'sine':'SuperHex Q14, positive clamp 16383','runtime':'Generate 256000-byte mask cache at startup; ASM copy into plane 2; FRAMES.BIN is verification fixture only'},indent=2)+'\n')
 print('Generated',len(frames),'bytes (32 x 8000)')
if __name__=='__main__':main()
