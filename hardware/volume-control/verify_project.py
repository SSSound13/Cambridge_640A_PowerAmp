"""Read-only saved-board checks; run with KiCad Python."""
from pathlib import Path
import json, math, hashlib, re
import pcbnew as p
R=Path(__file__).resolve().parent
u=p.LoadBoard(str(R/'ALPS_Adapter.kicad_pcb'))
l=p.LoadBoard(str(R/'Repair_Reference.kicad_pcb'))
uf={f.GetReference():f for f in u.GetFootprints()};lf={f.GetReference():f for f in l.GetFootprints()}
def xy(obj):return (p.ToMM(obj.GetPosition().x),p.ToMM(obj.GetPosition().y))
def project(pt):return (198.5-pt[1],pt[0]+13.7)
for n in range(1,5):assert math.dist(project(xy(uf['H'+str(n)])),xy(lf['H_ALPS'+str(n)]))<.00001
for q in uf['J1'].Pads():
 other=next(v for v in lf['J_ALPS'].Pads() if v.GetNumber()==q.GetNumber())
 assert math.dist(project(xy(q)),xy(other))<.00001
tracks=sorted((t.GetClass(),str(t.GetStart()),str(t.GetEnd()),t.GetWidth(),t.GetLayer(),t.GetNetname()) for t in l.GetTracks())
pads=sorted((f.GetReference(),q.GetNumber(),str(q.GetPosition()),str(q.GetSize()),str(q.GetDrillSize()),q.GetNetname()) for f in l.GetFootprints() for q in f.Pads())
assert hashlib.sha256(repr((tracks,pads)).encode()).hexdigest()==json.loads((R/'reference/package-validation.json').read_text())['geometry_fingerprint']
assert sum(1 for t in l.GetDrawings() if t.GetLayer()==p.User_1)==128
for name in ['VolumeControl','ALPS_Adapter']:
 for model in re.findall(r'\(model "([^"]+)"',(R/(name+'.kicad_pcb')).read_text()):
  assert model.startswith('${KIPRJMOD}/models/')
  assert (R/model.replace('${KIPRJMOD}/','')).is_file(),model
print('PASS: four axes, six pins, unchanged lower copper/pads, 128 factory polygons, all local model paths')
