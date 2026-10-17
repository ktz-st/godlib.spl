"""Extract the original one-bit BUGSY font."""
from pathlib import Path
import struct
root=Path(__file__).resolve().parents[1]
b=(root/'assets/BUGSY.MBK').read_bytes()
assert b[:10]==b'Lionpoubnk'
assert struct.unpack_from('>IHH',b,18)==(0x06071963,4,27)
# Native font header is 264 bytes, preceded by the 18-byte MBK wrapper.
(root/'assets/BUGSY.BIN').write_bytes(b[282:282+224*108])
