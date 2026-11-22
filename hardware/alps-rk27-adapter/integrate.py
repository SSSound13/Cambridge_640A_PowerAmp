"""Build corrected R3 and a separate, NON-FABRICATION KiCad assembly view."""
from pathlib import Path
import pcbnew as p
import json, shutil, subprocess, math
R=Path(__file__).resolve().parent
LOW=R.parent/'volume-control-repair'; LOW.mkdir(exist_ok=True)
I=R/'integration'; I.mkdir(exist_ok=True)
FP=Path(p.__file__).resolve().parents[1]/'share/kicad/footprints'
if not FP.exists(): FP=Path.home()/'AppData/Local/Programs/KiCad/10.0/share/kicad/footprints'
CLI=str(FP.parents[2]/'bin/kicad-cli.exe')
def mm(x,y): return p.VECTOR2I(p.FromMM(x),p.FromMM(y))
src=LOW/'Cambridge640A_R3_AS_RECEIVED.kicad_pcb'
if not src.exists(): shutil.copy2(Path.home()/'Downloads/Cambridge640A_R3_FACTORY_REFERENCE.kicad_pcb',src)
b=p.LoadBoard(str(src))
# The existing RM16 and balance pad centres already match the manual nominal grid.
# Keep their nets and holes; the manual does not dimension the drills.
b.RemoveAllItemsOnLayer(p.Edge_Cuts)
# Manual top corner: (114.00675 - 92.76601) * .635661 = 13.50 mm
# from balance centre. Rear edge stops 4 mm beyond the second screw row.
outline=[(60,36.5),(91,36.5),(91,73.7),(106,73.7),(106,129.7),(60,129.7)]
for a,c in zip(outline,outline[1:]+outline[:1]):
 e=p.PCB_SHAPE();e.SetShape(p.SHAPE_T_SEGMENT);e.SetStart(mm(*a));e.SetEnd(mm(*c));e.SetWidth(p.FromMM(.05));e.SetLayer(p.Edge_Cuts);b.Add(e)
holes=[]
for n,(x,y) in enumerate([(64.7,77.7),(64.7,125.7),(102,77.7),(102,125.7)],1):
 f=p.FootprintLoad(str(FP/'MountingHole.pretty'),'MountingHole_3.2mm_M3');f.SetFPID(p.LIB_ID('MountingHole','MountingHole_3.2mm_M3'));f.SetReference('H_ALPS'+str(n));f.SetPosition(mm(x,y));b.Add(f)
 f.Reference().SetVisible(False);f.Value().SetVisible(False)
 z=p.ZONE(b);z.SetIsRuleArea(True);z.SetLayerSet(p.LSET.AllCuMask());z.SetDoNotAllowTracks(True);z.SetDoNotAllowVias(True);z.SetDoNotAllowZoneFills(True);z.SetDoNotAllowPads(False);z.SetDoNotAllowFootprints(False)
 poly=z.Outline();poly.NewOutline()
 for k in range(64):
  v=mm(x+3.5*math.cos(k*math.tau/64),y+3.5*math.sin(k*math.tau/64));poly.Append(v.x,v.y)
 b.Add(z);holes.append({'reference':'H'+str(n),'main_x_mm':x,'main_y_mm':y,'adapter_x_mm':y-13.7,'adapter_y_mm':198.5-x,'diameter_mm':3.2})
# Reroute the three existing through-runs around the front-left mounting hole.
# Preserve their endpoints, layer, width and net; no electrical topology changes.
replacements=[]
for tr in list(b.GetTracks()):
 a=(p.ToMM(tr.GetStart().x),p.ToMM(tr.GetStart().y));c=(p.ToMM(tr.GetEnd().x),p.ToMM(tr.GetEnd().y))
 if a==(61.5,57.0) and c==(61.5,100.5) or a==(61.5,59.0) and c==(61.5,96.7):
  replacements.append((tr,[a,(61.5,71.7),(60.85,72.35),(60.85,83.05),(61.5,83.7),c]))
 elif a==(66.0,47.5) and c==(66.0,96.2):
  replacements.append((tr,[a,(66,70),(69,73),(69,82.4),(66,85.4),c]))
assert len(replacements)==3
for old,pts in replacements:
 for a,c in zip(pts,pts[1:]):
  t=p.PCB_TRACK(b);t.SetStart(mm(*a));t.SetEnd(mm(*c));t.SetWidth(old.GetWidth());t.SetLayer(old.GetLayer());t.SetNet(old.GetNet());b.Add(t)
 b.Remove(old)
# Landing pad row is a standard footprint. Electrical repair routing is separate work.
f=p.FootprintLoad(str(FP/'Connector_PinHeader_2.54mm.pretty'),'PinHeader_1x06_P2.54mm_Vertical');f.SetFPID(p.LIB_ID('Connector_PinHeader_2.54mm','PinHeader_1x06_P2.54mm_Vertical'));f.SetReference('J_ALPS');f.SetValue('ALPS landing pads - routing pending');f.SetOrientationDegrees(90);f.SetPosition(mm(73.5,78.7));f.Models().clear();b.Add(f)
f.Reference().SetVisible(False);f.Value().SetVisible(False)
for pad in f.Pads():
 name=['/AGND','/VOL_L','/IN_L','/AGND','/VOL_R','/IN_R'][int(pad.GetNumber())-1]
 pad.SetNet(b.FindNet(name))
text=p.PCB_TEXT(b);text.SetText('R3 + ALPS / MECHANICAL DRAFT\nJ_ALPS: ROUTING PENDING');text.SetPosition(mm(83,120));text.SetTextSize(mm(1,1));text.SetLayer(p.F_SilkS);b.Add(text)
for d in b.GetDrawings():
 if isinstance(d,p.PCB_TEXT) and d.GetText()=='L IN': d.SetPosition(mm(87,81.5))
dest=LOW/'Cambridge640A_R4_ALPS_MECHANICAL.kicad_pcb';p.SaveBoard(str(dest),b)
# Preserve received 0.6 mm thickness: it is a repair overlay, not a full parent PCB.
report={'source_thickness_mm':p.ToMM(b.GetDesignSettings().GetBoardThickness()),'front_edge_x_mm':60,'front_row_x_mm':63.5,'front_setback_mm':3.5,'old_pad_centres_unchanged':True,'old_drills_unchanged_mm':1.3,'old_pad_size_unchanged_mm':2.8,'volume_balance_axis_spacing_mm':48.7,'holes':holes,'landing_pins_unrouted':True,'height_between_top_surfaces_mm':8.5,'clear_gap_mm':6.9,'basis':'Nominal dimensions rounded from manual vector artwork; no dimensioned factory drilling drawing available.'}
report.update(balance_corner_mm=[60,36.5],balance_axis_to_side_edge_mm=13.5,lower_rear_edge_x_mm=106,adapter_overhang_mm=30.5,rerouted_existing_nets=['/AGND','/VOL_L','/VOL_R'])
(I/'two_board_alignment.json').write_text(json.dumps(report,indent=2))
# Transform lower geometry into adapter XY. Export with origin at adapter shaft.
for item in list(b.GetFootprints())+list(b.GetTracks())+list(b.GetDrawings())+list(b.Zones()):
 item.Rotate(mm(0,0),p.EDA_ANGLE(90,p.DEGREES_T));item.Move(mm(-13.7,198.5))
for f in b.GetFootprints(): f.Models().clear()
trans=I/'lower-positioned.kicad_pcb';p.SaveBoard(str(trans),b)
subprocess.run([CLI,'pcb','export','vrml','--force','--units','tenths','--user-origin','85x140mm','-o',str(I/'lower-board.wrl'),str(trans)],check=True)
trans.unlink()
upper=p.LoadBoard(str(R/'alps-rk27-adapter.kicad_pcb'))
for f in upper.GetFootprints():
 models=list(f.Models());f.Models().clear()
 for m in models:
  m.m_Filename=m.m_Filename.replace('${KIPRJMOD}/Adapter.3dshapes/','${KIPRJMOD}/../Adapter.3dshapes/')
  f.Add3DModel(m)
 if f.GetReference()=='J1': f.Models().clear()
# A model-only carrier, not a fabricated/custom component footprint.
carrier=p.FOOTPRINT(upper);carrier.SetReference('ASSEMBLY_ONLY');carrier.SetPosition(mm(85,140));carrier.Reference().SetVisible(False);carrier.Value().SetVisible(False)
m=p.FP_3DMODEL();m.m_Filename='${KIPRJMOD}/lower-board.wrl';m.m_Offset.z=-8.8;carrier.Add3DModel(m)
# Long pins are visual hardware only: 14.5 mm total, 0.64 mm square.
vrml='#VRML V2.0 utf8\n# Assembly hardware, mm converted to KiCad 0.1-inch model units.\n'
for i in range(6):
 x=-20;d=15+2.54*i
 vrml+=f'Transform {{ translation {x/2.54} {d/2.54} {-3.85/2.54} children [ Shape {{ appearance Appearance {{ material Material {{ diffuseColor .75 .6 .2 }} }} geometry Box {{ size {.64/2.54} {.64/2.54} {14.5/2.54} }} }} ] }}\n'
# Semitransparent cylinders denote M3 axes and 6.9 mm spacer envelopes, not selected screws.
for h in holes:
 x=h['adapter_x_mm']-85;d=140-h['adapter_y_mm']
 points=[((x+3*math.cos(k*math.tau/32))/2.54,(d+3*math.sin(k*math.tau/32))/2.54,z/2.54) for z in (-8.5,-1.6) for k in range(32)]
 faces=[tuple(range(31,-1,-1)),tuple(range(32,64))]+[(k,(k+1)%32,(k+1)%32+32,k+32) for k in range(32)]
 coords=', '.join(' '.join(str(v) for v in pt) for pt in points);indices=', '.join(' '.join(str(v) for v in face)+' -1' for face in faces)
 vrml+=f'Shape {{ appearance Appearance {{ material Material {{ diffuseColor .65 .65 .7 transparency .35 }} }} geometry IndexedFaceSet {{ solid TRUE coord Coordinate {{ point [ {coords} ] }} coordIndex [ {indices} ] }} }}\n'
(I/'assembly-hardware.wrl').write_text(vrml)
m=p.FP_3DMODEL();m.m_Filename='${KIPRJMOD}/assembly-hardware.wrl';carrier.Add3DModel(m);upper.Add(carrier)
p.SaveBoard(str(I/'two-board-assembly.kicad_pcb'),upper)
print('Built corrected lower PCB and assembly-only PCB')
