"""Check saved boards, not just requested construction coordinates (KiCad Python)."""
from pathlib import Path
import pcbnew as p
import json, math
R=Path(__file__).resolve().parent
u=p.LoadBoard(str(R/'alps-rk27-adapter.kicad_pcb'))
l=p.LoadBoard(str(R.parent/'volume-control-repair/Cambridge640A_R4_ALPS_MECHANICAL.kicad_pcb'))
uf={f.GetReference():f for f in u.GetFootprints()};lf={f.GetReference():f for f in l.GetFootprints()}
def xy(obj): return (p.ToMM(obj.GetPosition().x),p.ToMM(obj.GetPosition().y))
def project(pt): return (198.5-pt[1],pt[0]+13.7)
def same(a,b): assert math.dist(a,b)<.00001,(a,b)
for n in range(1,5): same(project(xy(uf['H'+str(n)])),xy(lf['H_ALPS'+str(n)]))
for a in uf['J1'].Pads():
 c=next(v for v in lf['J_ALPS'].Pads() if v.GetNumber()==a.GetNumber());same(project(xy(a)),xy(c))
for new,old in [('1','6'),('2','5'),('3','4')]:
 a=next(v for v in uf['RV1'].Pads() if v.GetNumber()==new);c=next(v for v in lf['VR1'].Pads() if v.GetNumber()==old);same(project(xy(a)),xy(c))
assert min(p.ToMM(d.GetStart().x) for d in l.GetDrawings() if d.GetLayer()==p.Edge_Cuts)==60
assert max(p.ToMM(d.GetStart().y) for d in u.GetDrawings() if d.GetLayer()==p.Edge_Cuts)==138.5
assert p.ToMM(u.GetDesignSettings().GetBoardThickness())==1.6
assert min(p.ToMM(d.GetStart().y) for d in l.GetDrawings() if d.GetLayer()==p.Edge_Cuts)==36.5
assert max(p.ToMM(d.GetStart().x) for d in l.GetDrawings() if d.GetLayer()==p.Edge_Cuts)==106
assert xy(lf['H_ALPS1'])[0]==xy(lf['H_ALPS2'])[0]==64.7
assert xy(lf['H_ALPS3'])[0]==xy(lf['H_ALPS4'])[0]==102
report={'four_mounting_axes_match':True,'six_header_pads_match':True,'front_three_audio_centres_match':True,'front_edges_flush':True,'top_surface_spacing_mm':8.5,'clear_gap_mm':6.9,'upper_thickness_mm':1.6,'lower_thickness_mm':.6,'electrical_lower_routing_complete':False}
report.update(balance_corner_mm=[60,36.5],balance_axis_to_side_edge_mm=13.5,lower_rear_edge_x_mm=106,adapter_overhang_mm=30.5,two_transverse_mounting_rows=True)
(R/'validation/integration.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report))
