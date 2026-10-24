from common import *

with HatariSession(str(staged()),hatari='/opt/homebrew/opt/hatari/Hatari.app/Contents/MacOS/hatari',tos=str(TOS),extra_args=['--confirm-quit','false','--memsize','1','--monitor','rgb','--fast-forward','true']) as h:
 p=Probe(h);p.put('gWipeBenchHold',1);p.put('gWipeBenchBackend',1);p.put('gWipeBenchEffect',0);dest=p.addr('gWipeBenchMemory')+16
 for closing in (0,1):
  p.put('gWipeBenchClosing',closing);p.put('gWipeBenchReset',1);p.request();assert p.val('gWipeBenchActual')==1
  previous=bytearray(p.raw(dest,32000));dirty=bytes((i*17+9)&255 for i in range(16));previous[:16]=dirty
  h.debug('w $'+format(dest,'x')+' '+' '.join('$'+format(b,'x') for b in dirty),settle=.02)
  p.request();actual=p.raw(dest,32000)
  if closing:
   words=struct.unpack('>16000H',previous);mask=[~w&65535 for w in MASKS[0][1]]
   expected=b''.join(struct.pack('>80H',*[words[y*80+x]&mask[y&15] for x in range(80)]) for y in range(200))
  else:expected=reference(0,1,0)
  assert actual==expected and not p.val('gWipeBenchAbiFailed'),closing
 p.put('gWipeBenchBackend',1);p.request(4);p.put('gWipeBenchHold',0);h.wait(.1)
 old=p.val('gVblOldHandler',4);h.control('hatari-event keydown 01');h.wait(.12);h.control('hatari-event keyup 01');h.wait(.3)
 assert p.val('gWipeExited') and int.from_bytes(p.raw(0x70,4),'big')==old
 result={'blitter_dirty_destination_cases':2,'opening_replaces_old_pixels':True,'closing_preserves_caller_changes':True,'full_buffer_checks':2,'byte_mismatches':0,'abi_preserved':True,'release_sha256':hashlib.sha256((APP/'WIPE.PRG').read_bytes()).hexdigest()}
 (APP/'dirty-verification.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
