#!/usr/bin/env python3
"""Build a private test mirror of the read-only UGH! reference source."""
from pathlib import Path
out=Path(__file__).resolve().parent
source=out.parents[2]/'ugh.agt/src/atari/tfmx_engine.asm'
s=source.read_text().replace('custom','TfmxRefCustom').replace('tfmxStubs','TfmxRefStubs')
s=s.replace('xref\tTfmxRefCustom','; private reference mirror').replace('xref\tTfmxRefStubs','; private reference stubs')
s=s.replace('SECTION S_0,CODE','SECTION .text,CODE').replace('\tEND\n','')
s+='\n        section .bss,bss\n        xdef TfmxRefCustom\nTfmxRefCustom: ds.b 256\nTfmxRefStubs: ds.b 16\n'
(out/'reference-core.s').write_text(s)
