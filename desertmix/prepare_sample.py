import sys
from pathlib import Path
pcm=Path(sys.argv[1]).read_bytes()
raw=bytes(((b if b<128 else b-256)//4)&255 for b in pcm)
raw+=bytes((-len(raw))%4)
Path(sys.argv[2]).write_bytes(raw)
print(f"{sys.argv[2]}: {len(raw)} bytes, 12517 Hz, gain 1/4")
