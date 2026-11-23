"""Rebuild assembly from saved editable boards without modifying the sources.
KiCad Python; no routing. Run KiCad CLI with normal user access.
"""
from pathlib import Path
import pcbnew as p
import math,json,subprocess,tempfile
R=Path(__file__).resolve().parent
CLI=str(Path(p.__file__).parent/'kicad-cli.exe')
if not Path(CLI).exists():CLI='C:/Users/Stas/AppData/Local/Programs/KiCad/10.0/bin/kicad-cli.exe'
def mm(x,y):return p.VECTOR2I(round(x*1e6),round(y*1e6))
def xy(obj):return (p.ToMM(obj.GetPosition().x),p.ToMM(obj.GetPosition().y))
def tracks(b):return sorted((str(t.GetStart()),str(t.GetEnd()),t.GetWidth(),t.GetLayer(),t.GetNetname()) for t in b.GetTracks())
lower=p.LoadBoard(str(R/'Repair_Reference.kicad_pcb'))
upper=p.LoadBoard(str(R/'ALPS_Adapter.kicad_pcb'))
# Read current boards without imposing old geometry on the user's edits.
report_path=R/'reference/three-supports.json'
report=json.loads(report_path.read_text())
holes=report['supports']
assert set(holes)=={'H1','H2','H3'}
# Position and export lower board for the assembly.
for item in list(lower.GetFootprints())+list(lower.GetTracks())+list(lower.GetDrawings())+list(lower.Zones()):
 item.Rotate(mm(0,0),p.EDA_ANGLE(90,p.DEGREES_T));item.Move(mm(-13.7,198.5))
for f in lower.GetFootprints():
 if f.GetReference() in ['R1','R2','R3','R4']:
  # Keep the current resistor bodies visible in the assembly.
  visual=p.FOOTPRINT(upper);visual.SetReference('ASSEMBLY_'+f.GetReference());visual.SetPosition(f.GetPosition());visual.SetOrientation(f.GetOrientation());visual.Reference().SetVisible(False);visual.Value().SetVisible(False)
  for source in f.Models():
   model=p.FP_3DMODEL();model.m_Filename=source.m_Filename;model.m_Offset.z=-8.2;visual.Add3DModel(model)
  upper.Add(visual)
 f.Models().clear()
with tempfile.TemporaryDirectory(prefix='volume-control-') as tmp:
 path=Path(tmp)/'lower.kicad_pcb';p.SaveBoard(str(path),lower)
 subprocess.run([CLI,'pcb','export','vrml','--force','--units','tenths','--user-origin','85x140mm','-o',str(R/'models/lower-board.wrl'),str(path)],check=True)
for f in upper.GetFootprints():
 if f.GetReference()=='J1':f.Models().clear()
carrier=p.FOOTPRINT(upper);carrier.SetReference('ASSEMBLY_ONLY');carrier.SetPosition(mm(85,140));carrier.Reference().SetVisible(False);carrier.Value().SetVisible(False)
for name,z in [('lower-board.wrl',-8.2),('assembly-hardware.wrl',0)]:
 m=p.FP_3DMODEL();m.m_Filename='${KIPRJMOD}/models/'+name;m.m_Offset.z=z;carrier.Add3DModel(m)
upper.Add(carrier);p.SaveBoard(str(R/'VolumeControl.kicad_pcb'),upper)
vrml='#VRML V2.0 utf8\n# Six pins and three spacer envelopes; not selected screws.\n'
for i in range(6):
 x=-20;d=15+2.54*i
 vrml+=f'Transform {{ translation {x/2.54} {d/2.54} {-3.85/2.54} children [ Shape {{ appearance Appearance {{ material Material {{ diffuseColor .75 .6 .2 }} }} geometry Box {{ size {.64/2.54} {.64/2.54} {14.5/2.54} }} }} ] }}\n'
for ref,(x0,y0) in holes.items():
 x=y0-98.7;d=x0-58.5
 pts=[((x+3*math.cos(k*math.tau/32))/2.54,(d+3*math.sin(k*math.tau/32))/2.54,z/2.54) for z in ((-7.9 if report['mounting_ownership'][ref]=='repair over main' else -8.5),-1.6) for k in range(32)]
 faces=[tuple(range(31,-1,-1)),tuple(range(32,64))]+[(k,(k+1)%32,(k+1)%32+32,k+32) for k in range(32)]
 coords=', '.join(' '.join(str(v) for v in pt) for pt in pts);indices=', '.join(' '.join(str(v) for v in f)+' -1' for f in faces)
 vrml+=f'Shape {{ appearance Appearance {{ material Material {{ diffuseColor .65 .65 .7 transparency .35 }} }} geometry IndexedFaceSet {{ solid TRUE coord Coordinate {{ point [ {coords} ] }} coordIndex [ {indices} ] }} }}\n'
(R/'models/assembly-hardware.wrl').write_text(vrml)
print('Assembly rebuilt from current editable boards; source boards unchanged.')
