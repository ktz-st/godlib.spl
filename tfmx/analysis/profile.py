#!/usr/bin/env python3
"""Same PRG/input/measurement window for both native mixers and both tunes."""
from pathlib import Path
import os,sys,time,tempfile,shutil,subprocess,json,hashlib
os.environ.setdefault('SDL_VIDEODRIVER','dummy');os.environ.setdefault('SDL_AUDIODRIVER','dummy')
sys.path.insert(0,str(Path.home()/'.agents/skills/hatari-debugging/scripts'))
from hatari_session import HatariSession,nm_symbols
from hrdb_profile import Rdb,profile_lines
root=Path(__file__).resolve().parents[1];out=root/'analysis';sy=nm_symbols(str(out/'TFMXDBG.PRG'),nm='m68k-atari-mintelf-nm');result={}
release_hash=hashlib.sha256((root/'TFMX.PRG').read_bytes()).hexdigest()
emulator='/opt/homebrew/opt/hatari-hrdb/Applications/hatari-hrdb/Hatari-HRDB.app/Contents/MacOS/Hatari'
with tempfile.TemporaryDirectory(prefix='tfmx-mixer-cpu-')as tmp:
 tmp=Path(tmp);dylib=tmp/'port.dylib';subprocess.run(['cc','-dynamiclib','-O2',str(out/'hrdb-port.c'),'-o',str(dylib)],check=True);os.environ['DYLD_INSERT_LIBRARIES']=str(dylib)
 for bank in [0]:
  for mixer in [0,1]:
   for rate in [1,2]:
    name=f'{"UGH"}-{["Lance","Leonard"][mixer]}-{rate}';folder=tmp/name;folder.mkdir();run=folder/'TFMX.PRG';shutil.copy2(root/'TFMX.PRG',run);assert hashlib.sha256(run.read_bytes()).hexdigest()==release_hash
    for p in list(root.glob('*.MDT'))+list(root.glob('*.SMP')):shutil.copy2(p,folder/p.name)
    with HatariSession(str(run),hatari=emulator,tos=str(Path.home()/'Atari/tos/TOS v1.62 (1990)(Atari Corp)(STE)(De).img'),sound=False,debug_except='bus,address,illegal',extra_args=['--confirm-quit','false','--memsize','4','--cpuclock','8','--cpulevel','0','--monitor','rgb'])as h:
     h.wait(9);base=h.basepage()['text'];a=lambda n:base+sy[n]
     def data(n,size=4):
      p=folder/'var.bin';p.unlink(missing_ok=True);h.debug(f'savebin {p} ${a(n):x} ${size:x}',settle=.08)
      for _ in range(100):
       if p.exists()and p.stat().st_size==size:return p.read_bytes()
       time.sleep(.01)
      raise AssertionError(h.lines[-20:])
     def val(n,size=4):return int.from_bytes(data(n,size),'big')
     def key(scan):h.control(f'hatari-event keydown 0x{scan:02x}',settle=.2);h.control(f'hatari-event keyup 0x{scan:02x}',settle=.2)
     def frames():
      before=val('gTfmxFrames');deadline=time.time()+25
      while val('gTfmxFrames')<before+3 and time.time()<deadline:h.wait(.1)
      assert val('gTfmxFrames')>=before+3
     deadline=time.time()+45
     while not val('gTfmxReady',2) and time.time()<deadline:h.wait(.15)
     assert val('gTfmxReady',2)==1
     if bank:key(50);frames()
     if mixer:key(48);frames()
     key(rate+1);frames()
     assert val('gTfmxMixer',2)==mixer and val('gTfmxBank',2)==bank and val('gTfmxRate',2)==rate
     work=val('spLeoWorkspace' if mixer else 'spPaulaWorkspace');workbytes=val('sLeoWorkspaceBytes' if mixer else 'sPaulaWorkspaceBytes');songbytes=int.from_bytes(data('info',12)[4:8],'big')
     # Restart the same slot while fast forwarding to the measurement boundary;
     # selection/loading/init are excluded. Both paths tick once per PAL VBL.
     start=val('gTfmxTicks');h.control('hatari-option --fast-forward true',settle=.1)
     deadline=time.time()+30
     while val('gTfmxTicks')-start<1000 and time.time()<deadline:h.wait(.15)
     h.control('hatari-option --fast-forward false',settle=.1)
     r=Rdb(port=56124);r.cmd('break',wait=1);r.cmd('profile 1');r.cmd('run');h.wait(12);r.cmd('break',wait=2);msg=r.take('!profile')
     for _ in range(5):
      if msg:break
      r.pump(1);msg=r.take('!profile')
     rows=profile_lines(msg);assert rows
     def region(first,last):return sum(c for pc,n,c in rows if a(first)<=pc<a(last))
     calls={pc:n for pc,n,c in rows};ticks=calls.get(a('Tfmx_Tick'),0);seq=calls.get(a('TfmxCore_Tick'),0);mixed=calls.get(a('voiceMixProcess'),0)//4 if mixer else seq;assert ticks>100 and abs(seq-mixed)<=1 and (seq<=ticks+1 if mixer else seq==ticks),(name,ticks,seq,mixed)
     core=region('TfmxCore_Begin','TfmxCore_End');outer=region('Tfmx_Tick','TfmxCore_Begin');generated=sum(c for pc,n,c in rows if work<=pc<work+workbytes)
     if mixer:
      adapter=region('TfmxDmaWrite','Tfmx_Tick');native=region('LeonardMixer_CodeBegin','LeonardMixer_CodeEnd')+region('LeonardMixer_Tick','LeonardMixer_CodeBegin')
     else:
      adapter=region('TfmxDmaWrite','Tfmx_Tick')+region('Tfmx_LancePrepare','PaulaMixer_GetWorkspaceSize');native=region('paula_calc','paula_channel_0')+region('PaulaMixer_Tick','PaulaMixer_Stop')
     helpers=0
     if not mixer:
      for first,last in [('memcpy','memset'),('memset','_setstack'),('__udivsi3','__subdf3')]:
       helpers+=region(first,last)
      native+=region('LeonardMixer_CodeBegin','LeonardMixer_CodeEnd')
     total=core+outer+native+adapter+generated+helpers
     result[name]={'audio_calls':ticks,'sequencer_calls':seq,'mixed_blocks':mixed,'cycles_per_vbl':round(total/ticks,2),'cpu_percent_8mhz_pal':round(total/ticks/1600,3),'song_bytes':songbytes,'workspace_bytes':workbytes,'resident_payload_bytes':songbytes+workbytes,'components_cycles_per_vbl':{k:round(v/ticks,2)for k,v in [('sequencer',core),('outer_tick',outer),('native_mixer',native),('voice_adapter',adapter),('generated_mixer',generated),('libc_helpers',helpers)]}}
     print(name,result[name],flush=True);r.cmd('profile 0');r.cmd('run');r.s.close()
assert hashlib.sha256((root/'TFMX.PRG').read_bytes()).hexdigest()==release_hash
report={'release_sha256':release_hash,'machine':'STE, 68000 8MHz, PAL, 4MiB, German TOS 1.62','method':'HRDB instruction cycles, identical release and 12s windows starting roughly 20s into UGH title subsong 0; rendering/input/loading excluded. Counts ALL native/adapter/sequencer ranges and generated mixer code in each workspace. Memory is requested resident song+workspace payload, excluding common PRG/screen/allocator overhead. Lance sequencer calls equal VBL calls; Leonard sequences per accepted PCM block, with at most one partial block at profile boundaries.','cases':result}
(out/'profile-mixers.json').write_text(json.dumps(report,indent=2)+'\n')
