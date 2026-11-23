"""Read-only drill audit of editable boards and assembly; write JSON report."""
from pathlib import Path
import json
import pcbnew as p
R=Path(__file__).resolve().parent
LIB=Path('C:/Users/Stas/AppData/Local/Programs/KiCad/10.0/share/kicad/footprints')
report={}
for name in ['ALPS_Adapter','Repair_Reference','VolumeControl']:
 b=p.LoadBoard(str(R/(name+'.kicad_pcb')));rows=[]
 for f in b.GetFootprints():
  ident=f.GetFPID();lib=str(ident.GetLibNickname());item=str(ident.GetLibItemName());standard=None
  if (LIB/(lib+'.pretty')/(item+'.kicad_mod')).exists():standard=p.FootprintLoad(str(LIB/(lib+'.pretty')),item)
  std={q.GetNumber():[p.ToMM(q.GetDrillSize().x),p.ToMM(q.GetDrillSize().y)] for q in standard.Pads()} if standard else {}
  for q in f.Pads():
   drill=[p.ToMM(q.GetDrillSize().x),p.ToMM(q.GetDrillSize().y)]
   if not drill[0]:continue
   rows.append({'reference':f.GetReference(),'pad':q.GetNumber(),'footprint':lib+':'+item,'drill_mm':drill,'copper_pad_mm':[p.ToMM(q.GetSize().x),p.ToMM(q.GetSize().y)],'xy_mm':[p.ToMM(q.GetPosition().x),p.ToMM(q.GetPosition().y)],'plated':q.GetAttribute()!=p.PAD_ATTRIB_NPTH,'matches_installed_standard_drill':drill==std[q.GetNumber()] if q.GetNumber() in std else None})
 report[name]={'hole_count':len(rows),'holes':rows}
def key(row):return (row['reference'],row['pad'],row['drill_mm'],row['xy_mm'])
report['assembly_matches_upper_drills']=sorted(map(key,report['ALPS_Adapter']['holes']))==sorted(map(key,report['VolumeControl']['holes']))
upper=[r for r in report['ALPS_Adapter']['holes'] if r['reference']=='J1'];lower=[r for r in report['Repair_Reference']['holes'] if r['reference']=='J_ALPS']
assert len(upper)==len(lower)==6
report['headers_match']=all(a['drill_mm']==c['drill_mm']==[1,1] and abs(198.5-a['xy_mm'][1]-c['xy_mm'][0])<1e-6 and abs(a['xy_mm'][0]+13.7-c['xy_mm'][1])<1e-6 for a,c in zip(sorted(upper,key=lambda r:r['pad']),sorted(lower,key=lambda r:r['pad'])))
assert report['headers_match'] and report['assembly_matches_upper_drills']
report['limits']=['VR1/VR4 1.3 mm are existing project drill sizes, not dimensions specified in Cambridge manual.','RK27 circular mounting holes 2.86 mm are supplied SamacSys geometry; ALPS drawing shows 2.6x1.2 mm rectangular holes. Physical fit remains to verify.','Balance RK163 standard footprint exists but matching model file is absent from official packages3D as checked 2026-11-24.']
(R/'validation/hole-audit.json').write_text(json.dumps(report,indent=2))
print({name:report[name]['hole_count'] for name in ['ALPS_Adapter','Repair_Reference','VolumeControl']});print('Assembly and six header drill positions/sizes match.')

