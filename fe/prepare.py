#!/usr/bin/env python3
from pathlib import Path
import math,re,struct,sys
ROOT=Path(__file__).resolve().parent
GOD=ROOT.parents[1]/'godlib'
sys.path.insert(0,str(GOD/'tools/toolbase'))
import toolbase as t
assets=ROOT/'assets';assets.mkdir(exist_ok=True)
# Use the exact built-in GodLib 8x8 glyphs, serialized as fixed-width BFBs.
raw=bytes(int(v,16)for v in re.findall(r'0x([0-9A-Fa-f]{2})',(GOD/'font8x8/fontdata.c').read_text()))
def font(dst,colour):
    frames=[]
    for c in range(32,127):
        pix=[0]*128;mask=[True]*128
        for y in range(8):
            for x in range(8):
                if raw[(c-32)*8+y]&(0x80>>x):pix[y*16+x]=colour;mask[y*16+x]=False
        frames.append(t.planar_sprite(16,8,4,4,pix,mask))
    spec=t.SpriteDef(font=True,charfirst=32,charlast=126,spacewidth=8)
    data=bytearray(t.serialize_bfb(frames,spec));data[10]=0
    table=struct.unpack_from('>I',data,28)[0]
    for i in range(95):struct.pack_into('>4H',data,table+i*8,0,0,7,7)
    struct.pack_into('>2H',data,12,8,8);dst.write_bytes(data)
font(assets/'NORMAL.BFB',10);font(assets/'ACTIVE.BFB',15);font(assets/'TITLE.BFB',15)
palette=[0x001,0x5cf,0x012,0x235,0x123,0x024,0x777,0x346,0x3ac,0x78e,0x2fd,0x57a,0xabc,0x09a,0xf80,0xffe]
for name,accent in [('MAIN',3),('OPTIONS',5)]:
    pix=[0]*64000
    def box(x,y,w,h,c):
        for row in range(y,y+h):pix[row*320+x:row*320+x+w]=[c]*w
    box(16,12,288,176,3);box(17,13,286,174,0)
    box(32,46,256,124,accent);box(33,47,254,122,2)
    box(32,46,256,2,10);box(32,169,256,1,3)
    for x in range(24,298,8):box(x,39,2,1,3);box(x,176,2,1,3)
    for x in (16,296):box(x,12,8,2,10);box(x,186,8,2,10)
    legend="ARROWS: ADJUST   ENTER: SELECT"
    for n,ch in enumerate(legend):
        for yy in range(8):
            for xx in range(8):
                if raw[(ord(ch)-32)*8+yy]&(0x80>>xx):pix[(178+yy)*320+44+n*8+xx]=6
    data=bytearray(32000)
    for y in range(200):
        for x in range(320):
            c=pix[y*320+x]
            for p in range(4):
                if c&(1<<p):
                    o=y*160+(x//16)*8+p*2;v=struct.unpack_from('>H',data,o)[0];struct.pack_into('>H',data,o,v|(0x8000>>(x&15)))
    (assets/(name+'.PI1')).write_bytes(bytes(2)+b''.join(t.u16be(v)for v in palette)+data)
col=[0]*128;transparent=[True]*128
for y in range(8):
    for x in range(7):
        if x<=3 and abs(y-3.5)<=x+1:col[y*16+x]=15;transparent[y*16+x]=False
(assets/'CURSOR.BSB').write_bytes(t.serialize_bsb([t.planar_sprite(16,8,4,4,col,transparent)]))
# Short decaying two-note chime, signed 8-bit 12.517 kHz mono.
rate=12517;raw=bytearray()
for i in range(3500):
    f=660 if i<1700 else 880;env=(1-(i%1700)/1700)if i<3400 else 0
    raw.append(round(70*env*math.sin(2*math.pi*f*i/rate))&255)
(assets/'CHIME.RAW').write_bytes(raw)
print('Prepared FE fonts, backgrounds, cursor and volume-test chime')
