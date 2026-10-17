"""Reproduce the static Control.EXW hscroll address mapping. Original is untouched."""
from pathlib import Path
import hashlib,struct,subprocess,tempfile,json
root=Path(__file__).resolve().parents[1]
p=root.parents[1]/'stos/CONTROL/EXTENSIO.NS/CONTROL.EXW';b=p.read_bytes()
assert b[:2]==b'\x60\x1a' and struct.unpack_from('>I',b,2)[0]==26290
assert b[b.index(b'hscroll')-1]==0xa7
# The tokenized WOBBLE.BAS command is EXT W:$a8; jump table begins at file $266.
entry=struct.unpack_from('>I',b,0x266+(0xa8-0x80)*4)[0];assert entry==0x1a2c
assert b[28+entry:28+entry+4]==bytes.fromhex('48f97ce0')
meta={'source':str(p),'sha256':hashlib.sha256(b).hexdigest(),'tos_header_bytes':28,'text_bytes':26290,'keyword_prefix':167,'basic_command_token':168,'jump_table_file_offset':0x266,'entry_text_offset':entry,'entry_file_offset':28+entry,'left_text_offset':0x1aa8,'left_one_pixel_text_offset':0x1c0a,'right_text_offset':0x1c70,'right_one_pixel_text_offset':0x1e1a,'core_end_text_offset':0x1e7e,'runtime_mapping':'extension_text_load_address + text_offset; runtime address not observed here'}
(root/'analysis/control-addresses.json').write_text(json.dumps(meta,indent=2)+'\n')
with tempfile.TemporaryDirectory() as td:
 raw=Path(td)/'hscroll.bin';raw.write_bytes(b[28+entry:28+0x1e7e])
 out=subprocess.check_output(['rg-dis',str(raw),'--cpu','68000','--org',hex(entry),'--annotate-offsets','--annotate-hw'],text=True)
 (root/'analysis/control-hscroll.s').write_text('; Control V3.06b by L.J.Greenhalgh, 1996. Analysis of local supplied binary.\n; Listing origins are TEXT-relative, not observed runtime addresses. File = TEXT + $1c.\n'+out)
print(json.dumps(meta,indent=2))
