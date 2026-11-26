"""KiCad geometry export/application for the explicitly authorized routing attempt."""
from pathlib import Path
import json,sys,re,tempfile,pcbnew as p
R=Path(__file__).resolve().parent
def xy(v):return [p.ToMM(v.x),p.ToMM(v.y)]
if sys.argv[1]=='export':
 data={}
 for name in ['ALPS_Adapter','Repair_Reference']:
  b=p.LoadBoard(str(R/(name+'.kicad_pcb')));pads=[]
  for f in b.GetFootprints():
   for q in f.Pads():
    pads.append(dict(id=f.GetReference()+'.'+q.GetNumber(),net=q.GetNetname(),xy=xy(q.GetPosition()),size=xy(q.GetSize()),angle=q.GetOrientationDegrees(),shape=int(q.GetShape()),smd=q.GetAttribute()==p.PAD_ATTRIB_SMD,npth=q.GetAttribute()==p.PAD_ATTRIB_NPTH,layers=[n for n,l in [('F.Cu',p.F_Cu),('B.Cu',p.B_Cu)] if q.IsOnLayer(l)]))
  data[name]={'pads':pads,'old_track_count':len(list(b.GetTracks()))}
 (R/'reference/routing-input.json').write_text(json.dumps(data,indent=2))
else:
 data=json.loads((R/'reference/routing-attempt.json').read_text())
 for name,report in data['boards'].items():
  if len(sys.argv)>2 and name!=sys.argv[2]:continue
  source=(R/(name+'.kicad_pcb')).read_text()
  source=re.sub(r'\n\t\((?:segment|via|arc)\b.*?\n\t\)', '',source,flags=re.S)
  with tempfile.TemporaryDirectory() as tmp:
   path=Path(tmp)/'clean.kicad_pcb';path.write_text(source);b=p.LoadBoard(str(path))
  assert not list(b.GetTracks())
  nets={q.GetNetname():q.GetNetCode() for f in b.GetFootprints() for q in f.Pads()}
  for route in report['routes']:
   for a,z in zip(route['points'],route['points'][1:]):
    t=p.PCB_TRACK(b);t.SetStart(p.VECTOR2I(round(a[0]*1e6),round(a[1]*1e6)));t.SetEnd(p.VECTOR2I(round(z[0]*1e6),round(z[1]*1e6)));t.SetWidth(p.FromMM(1));t.SetLayer(p.F_Cu if route['layer']=='F.Cu' else p.B_Cu);t.SetNetCode(nets[route['net']]);b.Add(t)
  p.SaveBoard(str(R/(name+'.kicad_pcb')),b)
 print('Replaced all old tracks; applied only reported new 1 mm routes.')
