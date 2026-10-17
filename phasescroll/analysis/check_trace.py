"""Validate the five display-register writes plus all 16 terrain palette words."""
import re

def check_trace(path,start,end,palette):
    writes=[]
    for line in path.read_text().splitlines():
        m=re.search(r'line_cyc_w=(\d+).*video_hbl_w=(\d+).*pc=(\w+)',line)
        if not m or not start<=int(m[3],16)<end:
            continue
        cycle,hbl=int(m[1]),int(m[2])
        kind=re.search(r'write ste video (ff820[579])',line)
        colour=re.search(r'write col addr=(\w+) col=(\w+)',line)
        if kind:
            name=kind[1];assert 'offset=0 ' in line,line
        elif 'write ste ff8265 ' in line:name='ff8265'
        elif 'write ste linewidth=' in line:name='linewidth'
        elif colour:
            name=colour[1]
            assert (hbl==102 and 376<=cycle<512) or (hbl==103 and 0<=cycle<56),line
            index=(int(name,16)-0xff8240)//2
            assert 0<=index<16 and int(colour[2],16)&0xfff==palette[index],line
        else:continue
        if not colour:assert hbl==102 and 376<=cycle<512,line
        writes.append((name,(hbl-102)*512+cycle))
    assert len(writes)>=2100 and len(writes)%21==0,len(writes)
    names=['ff8205','ff8207','ff8209','ff8265','linewidth']+[f'{i:x}' for i in range(0xff8240,0xff8260,2)]
    for i in range(0,len(writes),21):assert [v[0] for v in writes[i:i+21]]==names
    geometry=[w[1] for w in writes if w[0] in names[:5]]
    colours=[w[1] for w in writes if w[0] not in names[:5]]
    return {'split_frames':len(writes)//21,
            'all_five_write_cycles':[min(geometry),max(geometry)],
            'palette_write_cycles_from_hbl102_start':[min(colours),max(colours)]}
