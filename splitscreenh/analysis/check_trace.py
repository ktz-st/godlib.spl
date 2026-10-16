"""Validate complete five-register transitions from an existing video_ste trace."""
import re

def check_trace(path,start,end):
    writes=[]
    for line in path.read_text().splitlines():
        m=re.search(r'line_cyc_w=(\d+).*nHBL=(\d+).*pc=(\w+)',line)
        if not m or not start<=int(m[3],16)<end:
            continue
        kind=re.search(r'write ste video (ff820[579])',line)
        if kind:
            name=kind[1]
            assert 'offset=0 ' in line,line
        elif 'write ste ff8265 ' in line:
            name='ff8265'
        elif 'write ste linewidth=' in line:
            name='linewidth'
        else:
            continue
        assert int(m[2])==78 and 404<int(m[1])<512,line
        writes.append((name,int(m[1])))
    assert len(writes)>=500 and len(writes)%5==0,len(writes)
    for i in range(0,len(writes),5):
        assert [v[0] for v in writes[i:i+5]]==['ff8205','ff8207','ff8209','ff8265','linewidth']
    return {'split_frames':len(writes)//5,
            'all_five_write_cycles':[min(v[1] for v in writes),max(v[1] for v in writes)]}
