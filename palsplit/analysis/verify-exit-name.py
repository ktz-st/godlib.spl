"""Isolate TOS 1.62 autostart exit failure using a raster-free return-0 program."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess,sys,tempfile
sys.path.insert(0,str(Path.home()/'.codex/skills/hatari-debugging/scripts'))
from hatari_session import HatariSession
root=Path(__file__).resolve().parents[1]
workspace=root.parents[1]
rom=os.environ.get('HATARI_TOS162','/Users/kriss/Atari/tos/TOS v1.62 (1990)(Atari Corp)(STE)(GB)[STE TOS, Rev 2].img')
results=[]
with tempfile.TemporaryDirectory(prefix='pal-exit-name-') as td:
 td=Path(td);source=td/'noop.c';source.write_text('int main(void) { return 0; }\n')
 payload=td/'noop.prg';mini=workspace/'libcmini'
 subprocess.run(['m68k-atari-mintelf-gcc','-Os','-mshort','-mfastcall','-m68000','-nostdlib','-nostartfiles','-static','-o',str(payload),str(mini/'lib/mshort/mfastcall/crt0.o'),str(source),'-L'+str(mini/'lib/mshort/mfastcall'),'-lcmini','-lgcc'],check=True)
 digest=hashlib.sha256(payload.read_bytes()).hexdigest()
 for name in ('PALSPLIT.PRG','PALFX.PRG'):
  disk=td/name.split('.')[0];disk.mkdir();program=disk/name;shutil.copy2(payload,program)
  with HatariSession(str(program),machine='ste',sound=False,debug_except='bus,address,illegal',screenshot_dir=str(root/'analysis/shots'/'exit-name'/name),extra_args=['--confirm-quit','false','--memsize','4','--cpuclock','8','--tos',rom]) as h:
   h.wait(12)
   faults=[line for line in h.lines if 'Bus Error' in line or 'Address Error' in line]
   h.screenshot()
   result=dict(filename=name,sha256=digest,source='int main(void) { return 0; }',tos='1.62',faults=faults)
   results.append(result);print(json.dumps(result),flush=True)
   if name=='PALFX.PRG':assert not faults
(root/'analysis/exit-name-results.json').write_text(json.dumps(results,indent=2)+'\n')
