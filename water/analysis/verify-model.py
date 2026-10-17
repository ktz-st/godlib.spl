"""Independent translation of the original Copper WAIT/modulo event stream."""
from pathlib import Path
import hashlib,json,re,struct
r=Path(__file__).resolve().parents[1];m=json.loads((r/'assets/wave.json').read_text());top=m['water_top'];height=m['height'];hold=m['hold_y']
# The table is copied as WAIT + Amiga modulo, independently of the row generator.
copper=[(6,160),(1,-40),(4,160),(1,-40),(6,160),(1,360),(4,160),(1,360),(7,160),(1,-40),(5,160),(1,-40),(7,160),(1,360),(5,160),(1,360),(8,160),(1,-40),(6,160),(1,-40),(8,160),(1,360),(6,160),(1,360)]
def reference(phase,remaining):
 events=[];beam=top+remaining
 while beam<=hold:
  wait,mod=copper[phase];events.append((beam,mod));beam+=wait;phase=(phase+1)%24
 events.append((hold,-40));pos=top*200;mod=160;index=0;rows=[]
 for y in range(top,200):
  while index<len(events) and events[index][0]<=y:mod=events[index][1];index+=1
  rows.append(min(pos//200,199));pos+=40+mod
 return rows
if __name__=='__main__':
 raw=(r/'assets/ROWS.BIN').read_bytes();tables=struct.unpack('>'+str(len(raw)//2)+'H',raw)
 assert len(tables)==86*height
 assert {(v['phase'],v['remaining']) for v in m['states']}=={(p,n) for p,(wait,_) in enumerate(copper) for n in range(1,wait+1)}
 for tick,v in enumerate(m['states']):
  rows=reference(v['phase'],v['remaining']);assert all(top<=y<200 for y in rows)
  assert list(tables[tick*height:(tick+1)*height])==[y*160 for y in rows],tick
 assert list(tables[84*height:85*height])==list(range(top*160,32000,160))
 assert all(v==0xffff for v in tables[85*height:])
 source=r.parents[1]/'ugh.agt/src/openugh/intro_water_wave.h'
 if source.exists():
  text=source.read_text()
  def array(name):return list(map(int,re.search(name+r'\[.*?\]\s*=\s*\{(.*?)\}',text,re.S)[1].replace('\n','').replace(' ','').split(',')))
  assert array('ughIntroWaveLength')==[v[0] for v in copper]
  assert array('ughIntroWaveAdvance')==[(40+v[1])//200 for v in copper]
  sha=hashlib.sha256(source.read_bytes()).hexdigest()
 else:sha=None
 result={'original_ugh_source_sha256':sha,'all_84_states_match_independent_copper_events':True,'water_top':top,'water_rows':height,'hold_y':hold,'all_reads_inside_water_region':True,'identity_and_invalid_tables_passed':True}
 (r/'analysis/model-results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
