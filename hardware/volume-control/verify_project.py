from pathlib import Path
import json,math,hashlib,re
import pcbnew as p
R=Path(__file__).resolve().parent;u=p.LoadBoard(str(R/'ALPS_Adapter.kicad_pcb'));l=p.LoadBoard(str(R/'Repair_Reference.kicad_pcb'));uf={f.GetReference():f for f in u.GetFootprints()};lf={f.GetReference():f for f in l.GetFootprints()}
def xy(o):return (p.ToMM(o.GetPosition().x),p.ToMM(o.GetPosition().y))
def project(v):return (198.5-v[1],v[0]+13.7)
holes=json.loads((R/'reference/three-supports.json').read_text())['supports']
for ref,pt in holes.items():assert math.dist(project(xy(uf[ref])),pt)<.00001
assert 'H4' not in uf and {f for f in lf if f.startswith('H_ALPS')}=={'H_ALPS1'}
for q in uf['J1'].Pads():assert math.dist(project(xy(q)),xy(next(v for v in lf['J_ALPS'].Pads() if v.GetNumber()==q.GetNumber())))<.00001
for c in json.loads((R/'reference/edge-solder-alignment.json').read_text())['contacts']:assert math.dist(xy(lf[c['reference']]),c['xy_mm'])<.00001
transfer=json.loads((R/'reference/user-routing-transfer.json').read_text())
for name,board in [('ALPS_Adapter',u),('Repair_Reference',l)]:
 actual=sorted([[t.GetNetname(),[t.GetStart().x,t.GetStart().y],[t.GetEnd().x,t.GetEnd().y],t.GetWidth(),t.GetLayerName()] for t in board.GetTracks()])
 expected=transfer[name]['tracks_before']
 if name=='ALPS_Adapter':expected=sorted([row[:-1]+['B.Cu' if row[-1]=='F.Cu' else 'F.Cu'] for row in expected])
 assert actual==expected,'User routing changed beyond authorized layer transfer'
 for f in board.GetFootprints():
  if f.GetReference() in ['H1','H2','H3','H_ALPS1']:
   assert f.GetFPID().GetLibItemName()=='MountingHole_3mm'
   assert all(q.GetDrillSize().x==p.FromMM(3) for q in f.Pads())
assert xy(uf['J2'])==(103,113)
assert not any(isinstance(d,p.PCB_TEXT) and d.GetText().startswith('RK27') for d in u.GetDrawings())
assert {(round(p.ToMM(d.GetStart().x),4),round(p.ToMM(d.GetStart().y),4)) for d in l.GetDrawings() if d.GetLayer()==p.Edge_Cuts}=={(60,36.5),(91,36.5),(91,109.5),(60,109.5)}
window=json.loads((R/'reference/factory-copper-window.json').read_text())
assert sum(d.GetLayer()==p.User_1 for d in l.GetDrawings())==len(window['copper_components'])
for name in ['VolumeControl','ALPS_Adapter']:
 for m in re.findall(r'\(model "([^"]+)"',(R/(name+'.kicad_pcb')).read_text()):assert (R/m.replace('${KIPRJMOD}/','')).is_file()
meshes=re.findall(r'point \[ (.*?) \]',(R/'models/ALPS_RK27112MC_envelope.wrl').read_text());assert len(meshes)==22;assert abs(max(float(pt.split()[1])*2.54 for mesh in meshes for pt in mesh.split(','))-66.7)<.00001
assert min(p.ToMM(d.GetStart().y) for d in u.GetDrawings() if d.GetLayer()==p.Edge_Cuts)==70.3
print('PASS: user routing preserved exactly (upper F/B exchanged); standard 3 mm holes; mechanics and models checked')
