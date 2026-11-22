"""Refresh manual user layers in the existing repair board; never route copper."""
from pathlib import Path
import json,hashlib
import pcbnew as p
R=Path(__file__).resolve().parent
M=R/"models"
b=p.LoadBoard(str(R/"Repair_Reference.kicad_pcb"))
def fingerprint(b):
 tracks=sorted((t.GetClass(),str(t.GetStart()),str(t.GetEnd()),t.GetWidth(),t.GetLayer(),t.GetNetname()) for t in b.GetTracks())
 pads=sorted((f.GetReference(),q.GetNumber(),str(q.GetPosition()),str(q.GetSize()),str(q.GetDrillSize()),q.GetNetname()) for f in b.GetFootprints() for q in f.Pads())
 return hashlib.sha256(repr((tracks,pads)).encode()).hexdigest()
before=fingerprint(b)
data=json.loads((R/'reference/factory-copper.json').read_text())
def mm(pt):return p.VECTOR2I(round(pt[0]*1e6),round(pt[1]*1e6))
for layer in [p.User_1,p.User_2,p.User_3,p.User_4]:b.RemoveAllItemsOnLayer(layer)
for c in data['copper_components']:
 poly=p.SHAPE_POLY_SET();poly.NewOutline()
 for pt in c['exterior'][:-1]:poly.Append(mm(pt))
 for ring in c['holes']:
  hole=poly.NewHole()
  for pt in ring[:-1]:poly.Append(mm(pt),-1,hole)
 poly.Fracture()
 shape=p.PCB_SHAPE(b);shape.SetShape(p.SHAPE_T_POLY);shape.SetPolyShape(poly);shape.SetFilled(True);shape.SetWidth(0);shape.SetLayer(p.User_1);b.Add(shape)
def line(a,z,layer,width=.15):
 d=p.PCB_SHAPE(b);d.SetShape(p.SHAPE_T_SEGMENT);d.SetStart(mm(a));d.SetEnd(mm(z));d.SetWidth(p.FromMM(width));d.SetLayer(layer);b.Add(d)
def label(txt,pt,layer,size=1):
 d=p.PCB_TEXT(b);d.SetText(txt);d.SetPosition(mm(pt));d.SetTextSize(mm((size,size)));d.SetTextThickness(p.FromMM(.15));d.SetLayer(layer);b.Add(d)
for pts in data['factory_outline']:
 for a,z in zip(pts,pts[1:]):line(a,z,p.User_4)
pts=[(60,73.7),(136.5,73.7),(136.5,129.7),(60,129.7),(60,73.7)]
for a,z in zip(pts,pts[1:]):line(a,z,p.User_3,.3)
for h in data['drill_checks']:
 x,y=h['xy']
 for radius in (1.6,3.5):
  d=p.PCB_SHAPE(b);d.SetShape(p.SHAPE_T_CIRCLE);d.SetCenter(mm((x,y)));d.SetEnd(mm((x+radius,y)));d.SetWidth(p.FromMM(.15));d.SetLayer(p.User_3);b.Add(d)
 label(h['ref']+(' FACTORY CUTOUT' if h['ref']=='H2' else (' COPPER HIT' if h['components'] else ' CLEAR')),(x+5,y-4),p.User_2,.8)
for a in data['anchors']:label(a['ref']+'.'+str(a['pad']),(a['xy'][0]+1.5,a['xy'][1]),p.User_2,.6)
label('User.1: MANUAL BOTTOM COPPER - REFERENCE ONLY',(110,28),p.User_2)
label('User.3: UPPER BOARD PROJECTION / User.4: FACTORY EDGE',(110,31),p.User_2)
p.SaveBoard(str(R/'Repair_Reference.kicad_pcb'),b)
after=fingerprint(p.LoadBoard(str(R/'Repair_Reference.kicad_pcb')))
assert before==after,'Copper or pads changed'
(R/'reference/package-validation.json').write_text(json.dumps({'copper_and_pads_unchanged':True,'geometry_fingerprint':after,'model_files':[f.name for f in M.iterdir()]},indent=2))
print('Project packaged; lower copper and pads unchanged')
