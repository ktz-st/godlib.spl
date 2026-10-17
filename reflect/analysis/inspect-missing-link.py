"""Extract and map actual REFLECT machine code, preserving supplied extension."""
from pathlib import Path
import hashlib,json,struct,subprocess
r=Path(__file__).resolve().parents[1]
p=r.parents[1]/'stos/mislink/mislink/STOS/LINK2.EXR';b=p.read_bytes();t=b[28:]
assert b[:2]==b'\x60\x1a' and struct.unpack_from('>I',b,2)[0]==22304
assert t[t.index(b'reflect')-1]==0x85
assert struct.unpack_from('>I',t,0x134+6*4)[0]==0x15da
steps=struct.unpack('>1600H',t[0x1712:0x2392]);assert all(v==steps[i%20] for i,v in enumerate(steps))
meta={'source':str(p),'sha256':hashlib.sha256(b).hexdigest(),'tos_header_bytes':28,'text_bytes':22304,'keyword_prefix':133,'basic_command_token':134,'jump_table_text_offset':308,'entry_text_offset':5594,'entry_file_offset':5622,'core_text_offset':5698,'core_file_offset':5726,'copy_loop_text_offset':5830,'return_to_stos_text_offset':5884,'state_text_offset':5902,'steps_text_offset':5906,'steps_words':1600,'steps_period_rows':[v//160 for v in steps[:20]],'line_offsets_text_offset':16768,'runtime_mapping':'extension TEXT load address + TEXT offset (no original STOS runtime observed)'}
(r/'analysis/missing-link-addresses.json').write_text(json.dumps(meta,indent=2)+'\n')
# Disassemble code only; the following words are DATA, not instructions.
listing=subprocess.check_output(['rg-dis',str(p),'--cpu','68000','--annotate-offsets'],text=True)
listing=listing[listing.index('_L15DA:'):listing.index('_L170E:')]
(r/'analysis/missing-link-reflect.s').write_text('; Original LINK2.EXR, TEXT-relative listing. File = TEXT + $1c.\n; Extract from full-file disassembly; external parser/return labels refer to the original extension.\n'+listing+'\n; $170e: dc.w 0,0 ; toggle, phase bytes\n; $1712: rept 80\n; dc.w '+','.join(str(v) for v in steps[:20])+'\n; endr\n; $4180: 200 words y*160\n')
# Unmodified executable core, except its STOS-specific exit is replaced by RTS.
# All PC-relative state/table operands retain their exact displacement.
raw=bytearray(t[0x1642:0x4310]);assert raw[0xba:0xc0]==bytes.fromhex('41f900005698')
raw[0xba:0xbc]=b'\x4e\x75'
(r/'analysis/original-core.bin').write_bytes(raw)
print(json.dumps(meta,indent=2))
