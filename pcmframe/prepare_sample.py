"""Reuse the mixer demo's signed 12517-Hz mono voice, with mixing headroom."""
from pathlib import Path
import sys

source = Path(sys.argv[1]).read_bytes()
pcm = bytes((int((v if v < 128 else v - 256) / 4) & 255) for v in source)
pcm += bytes((-len(pcm)) % 250)
assert 0 < len(pcm) <= 63750
Path(sys.argv[2]).write_bytes(pcm)
print(f'{len(source)} -> {len(pcm)} bytes, {len(pcm)//250} blocks, gain 1/4')
