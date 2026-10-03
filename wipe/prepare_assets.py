"""Convert generated RGB artwork to individual-palette ST-low Degas PI1 files.
Requires Pillow. Originals remain in assets/; previews show the final indices.
"""
from pathlib import Path
import struct
import sys
from PIL import Image
ROOT=Path(__file__).resolve().parent
def st_word(colour):
    channels=[round(v*7/255) for v in colour]
    return (channels[0]<<8)|(channels[1]<<4)|channels[2]
def st_rgb(word):
    return tuple(round(((word>>shift)&7)*255/7) for shift in (8,4,0))
for name in (sys.argv[1:] or ('coast','space','forest')):
    image=Image.open(ROOT/'assets'/f'{name}.png').convert('RGB')
    image=image.resize((320,200),Image.Resampling.LANCZOS)
    # Fourteen scene colours plus reserved black/white for wipes and captions.
    reduced=image.quantize(colors=14,method=Image.Quantize.MEDIANCUT)
    colours=reduced.getpalette()[:42]
    words=[]
    for i in range(0,42,3):
        word=st_word(colours[i:i+3])
        if word not in (0,0x777) and word not in words: words.append(word)
    # Quantized RGB colours can collapse to the same 3-bit ST colour.
    for level in range(1,7):
        if len(words)>=14: break
        word=level*0x111
        if word not in words: words.append(word)
    while len(words)<14: words.append(words[-1])
    PALETTE=[0]+words[:14]+[0x777]
    pal=Image.new('P',(1,1))
    pal.putpalette([v for word in PALETTE for v in st_rgb(word)]+[0]*(768-48))
    indexed=image.quantize(palette=pal,dither=Image.Dither.FLOYDSTEINBERG)
    pixels=list(indexed.tobytes())
    assert max(pixels)<16
    data=bytearray(struct.pack('>17H',0,*PALETTE))
    for y in range(200):
        for x in range(0,320,16):
            for plane in range(4):
                word=sum(((pixels[y*320+x+i]>>plane)&1)<<(15-i) for i in range(16))
                data.extend(struct.pack('>H',word))
    assert len(data)==32034
    (ROOT/f'{name.upper()}.PI1').write_bytes(data)
    indexed.convert('RGB').save(ROOT/'assets'/f'{name}-st.png')
    # Decode the emitted planes independently to catch packing/order mistakes.
    for y in range(200):
        for x in range(320):
            group=34+y*160+(x//16)*8
            words=struct.unpack_from('>4H',data,group)
            value=sum(((words[p]>>(15-x%16))&1)<<p for p in range(4))
            assert value==pixels[y*320+x]
    print(f'{name.upper()}.PI1: 320x200, 16 ST colours, {len(data)} bytes')
