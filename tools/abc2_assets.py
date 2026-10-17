"""Offline ABC2 conversion: original RGB -> one STE palette, no dithering.
ABC2 defaults to a black entry 0; callers may reserve semantic colours.
The emitted palette and Atari bitplanes are decoded and verified against
ABC2's RGB444 preview before they are used by any example.
"""
from pathlib import Path
from PIL import Image
import hashlib,json,os,struct,subprocess,tempfile
ROOT=Path(__file__).resolve().parents[1]
def rgb(word):
    return tuple(((((word>>s)&7)<<1)|(((word>>s)>>3)&1))*17 for s in (8,4,0))
def pack(indices,width,height,planes=4):
    assert width%16==0 and len(indices)==width*height
    out=bytearray()
    for y in range(height):
        for x in range(0,width,16):
            for p in range(planes):
                out+=struct.pack('>H',sum(((indices[y*width+x+i]>>p)&1)<<(15-i) for i in range(16)))
    return bytes(out)
def convert(image,planes=4,locks=None):
    image=image.convert('RGB');w,h=image.size;assert w%16==0
    exe=Path(os.environ.get('ABC2',str(ROOT.parent/'abc/abc2'))).resolve()
    if not exe.is_file():raise FileNotFoundError('Build abc/abc2 or set ABC2 to the executable')
    with tempfile.TemporaryDirectory(prefix='godlib-abc2-') as td:
        td=Path(td);image.save(td/'source.png')
        args=[str(exe),'source.png','-bpc',str(planes),'-atari','-ste','-quantize','-cpu']
        for index,colour in sorted((locks or {}).items()):args+=['-forcecolor',str(index),f'{colour:03x}']
        args+=['-b','image.gfx','-p','image.pal','-preview','preview.png']
        done=subprocess.run(args,cwd=td,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        if done.returncode:raise RuntimeError(done.stdout)
        raw=(td/'image.gfx').read_bytes();pal=(td/'image.pal').read_bytes()
        assert len(raw)==w*h*planes//8 and len(pal)==2*(1<<planes)
        words=list(struct.unpack('>'+str(1<<planes)+'H',pal));assert all(v<=0xfff for v in words)
        indices=[]
        for y in range(h):
            for x in range(0,w,16):
                values=struct.unpack_from('>'+str(planes)+'H',raw,(y*w//16+x//16)*planes*2)
                indices.extend(sum(((values[p]>>(15-i))&1)<<p for p in range(planes)) for i in range(16))
        preview=Image.new('RGB',(w,h));palette=[rgb(v) for v in words]
        preview.putdata([palette[i] for i in indices])
        assert preview.tobytes()==Image.open(td/'preview.png').convert('RGB').tobytes()
        assert raw==pack(indices,w,h,planes)
        meta={'converter':done.stdout.splitlines()[0],'arguments':args[1:],'source_rgb_sha256':hashlib.sha256(image.tobytes()).hexdigest(),'size':[w,h],'planes':planes,'gamut':'STE RGB444 / 4096 colours','dithering':False,'palette_words':[hex(v) for v in words],'used_colours':len(set(indices)),'all_exported_pixels_verified':True}
        return words,indices,preview,meta

def save(image,output,preview,planes=4,locks=None,header=True):
    words,indices,im,meta=convert(image,planes,locks)
    payload=pack(indices,*image.size,4)
    palette=struct.pack('>16H',*(words+[0]*(16-len(words))))
    data=(b'\0\0' if header else b'')+palette+payload
    Path(output).write_bytes(data);im.save(preview)
    Path(str(preview)+'.json').write_text(json.dumps(meta,indent=2)+'\n')
    return words,indices
