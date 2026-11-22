"""Sync mounting axes from Repair_Reference, trim adapter and rebuild assembly.
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
saved_tracks=tracks(upper)
lower_outline=[(p.ToMM(d.GetStart().x),p.ToMM(d.GetStart().y)) for d in lower.GetDrawings() if d.GetLayer()==p.Edge_Cuts]
holes=json.loads((R/'reference/three-supports.json').read_text())['supports']
for f in lower.GetFootprints():
 if f.GetReference().startswith('H_ALPS'):holes[f.GetReference().replace('H_ALPS','H')]=xy(f)
assert set(holes)=={'H1','H2','H3'}
for f in list(upper.GetFootprints()):
 ref=f.GetReference()
 if ref not in ('H1','H2','H3','H4'):continue
 old=xy(f)
 zones=[z for z in upper.Zones() if z.GetIsRuleArea() and math.dist(xy(z),(old[0]+3.5,old[1]))<.01]
 if ref not in holes:
  for z in zones:upper.Remove(z)
  upper.Remove(f)
 else:
  x,y=holes[ref];new=(y-13.7,198.5-x);delta=mm(new[0]-old[0],new[1]-old[1]);f.Move(delta)
  for z in zones:z.Move(delta)
# D=66.7 mm is the motor rear cap; no vertical terminal PCB per user inspection.
rear=69.7;new_y=140-rear
outline=[(60,138.5),(110.7,138.5),(110.7,70.3),(80,70.3),(60,90)]
upper.RemoveAllItemsOnLayer(p.Edge_Cuts)
for a,z in zip(outline,outline[1:]+outline[:1]):
 d=p.PCB_SHAPE(upper);d.SetShape(p.SHAPE_T_SEGMENT);d.SetStart(mm(*a));d.SetEnd(mm(*z));d.SetWidth(p.FromMM(.05));d.SetLayer(p.Edge_Cuts);upper.Add(d)
for f in upper.GetFootprints():
 if f.GetReference()=='J2':f.SetPosition(mm(103,113));f.SetOrientationDegrees(0)
assert saved_tracks==tracks(upper)
for d in list(upper.GetDrawings()):
 if not isinstance(d,p.PCB_TEXT):continue
 text=d.GetText()
 if text=='H4':upper.Remove(d)
 elif text=='H2':d.SetPosition(mm(105.3,133.0))
 elif text.startswith('FRONT DATUM:'):d.SetLayer(p.Dwgs_User)
 elif text in ('RK27 ADAPTER - DRAFT','RK27 / 3 SUPPORTS'):
  upper.Remove(d)
 elif text=='J2 MOTOR':d.SetPosition(mm(104,118))
p.SaveBoard(str(R/'ALPS_Adapter.kicad_pcb'),upper)
# Update projected outline without disturbing factory artwork or working copper.
for d in list(lower.GetDrawings()):
 if d.GetLayer()==p.User_3 and isinstance(d,p.PCB_SHAPE) and d.GetShape()==p.SHAPE_T_SEGMENT:
  lower.Remove(d)
 if isinstance(d,p.PCB_TEXT):
  text=d.GetText()
  if text.startswith('H1 COPPER HIT'):d.SetText('H1 / FACTORY Cu REMOVED')
  elif text.startswith('H2 FACTORY CUTOUT') or text.startswith('H2 CLEAR'):
   d.SetText('H2 / 3 SUPPORTS');d.SetPosition(mm(68.75,110))
  elif text.startswith('H4 COPPER HIT'):d.SetText('FACTORY Cu UNDER REPAIR: REMOVE');d.SetPosition(mm(90,125))
projection=[(198.5-y,x+13.7) for x,y in outline]
for a,z in zip(projection,projection[1:]+projection[:1]):
 d=p.PCB_SHAPE(lower);d.SetShape(p.SHAPE_T_SEGMENT);d.SetStart(mm(*a));d.SetEnd(mm(*z));d.SetWidth(p.FromMM(.3));d.SetLayer(p.User_3);lower.Add(d)
p.SaveBoard(str(R/'Repair_Reference.kicad_pcb'),lower)
# Position and export lower board for the assembly.
for item in list(lower.GetFootprints())+list(lower.GetTracks())+list(lower.GetDrawings())+list(lower.Zones()):
 item.Rotate(mm(0,0),p.EDA_ANGLE(90,p.DEGREES_T));item.Move(mm(-13.7,198.5))
for f in lower.GetFootprints():f.Models().clear()
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
 pts=[((x+3*math.cos(k*math.tau/32))/2.54,(d+3*math.sin(k*math.tau/32))/2.54,z/2.54) for z in ((-7.9 if ref=='H1' else -8.5),-1.6) for k in range(32)]
 faces=[tuple(range(31,-1,-1)),tuple(range(32,64))]+[(k,(k+1)%32,(k+1)%32+32,k+32) for k in range(32)]
 coords=', '.join(' '.join(str(v) for v in pt) for pt in pts);indices=', '.join(' '.join(str(v) for v in f)+' -1' for f in faces)
 vrml+=f'Shape {{ appearance Appearance {{ material Material {{ diffuseColor .65 .65 .7 transparency .35 }} }} geometry IndexedFaceSet {{ solid TRUE coord Coordinate {{ point [ {coords} ] }} coordIndex [ {indices} ] }} }}\n'
(R/'models/assembly-hardware.wrl').write_text(vrml)
report={'supports':holes,'adapter_rear_D_mm':rear,'motor_rear_envelope_D_mm':66.7,'rear_margin_mm':3,'adapter_size_mm':[50.7,68.2],'adapter_outline_mm':outline,'adapter_projection_mm':projection,'motor_connector_xy_mm':[103,113],'gearbox_right_X_mm':22.7,'right_margin_mm':3,'tracks_unchanged':True,'factory_copper_under_repair_removed_by_user':True,'status':'Mechanical review; no routing'}
report['repair_outline_mm']=lower_outline
report.update(repair_size_mm=[31,73],repair_end_y_mm=109.5,mounting_ownership={'H1':'repair over main','H2':'main only','H3':'main only'},main_to_adapter_top_mm=8.5,repair_top_above_main_mm=.6,clear_gap_above_repair_mm=6.3,pending_routing='J1-J5 aligned to original factory copper; J6 added for second ground branch. All original tracks unchanged; boundary connections need rerouting.')
if (R/'reference/routing-attempt.json').exists():
 report.update(status='User-authorized bounded routing attempt; see routing-attempt.json',tracks_unchanged=False,sync_preserves_existing_tracks=True,pending_routing='See routing-attempt.json for remaining disconnected groups. Old routing was explicitly removed and replaced.')
(R/'reference/three-supports.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report))
