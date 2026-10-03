"""Prepare the existing 12517-Hz signed mono voice for both DMA rates."""
from pathlib import Path
import sys
source=Path(sys.argv[1]).read_bytes()
values=[int((b if b<128 else b-256)/4) for b in source]
for rate,filename in [(12517,'VOICE12.RAW'),(25033,'VOICE25.RAW')]:
    output=bytearray()
    for i in range((len(values)*rate+12516)//12517):
        pos=i*12517
        j,frac=divmod(pos,rate)
        a=values[min(j,len(values)-1)]
        b=values[min(j+1,len(values)-1)]
        output.append(round((a*(rate-frac)+b*frac)/rate)&255)
    output.extend(bytes((-len(output))%512))
    Path(filename).write_bytes(output)
    print(filename, len(output), 'bytes; signed mono, gain 1/4, padded to 512')
