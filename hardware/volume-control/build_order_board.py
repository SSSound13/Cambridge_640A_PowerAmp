"""Join the two saved 0.5 mm PCBs with two 3 mm tabs and a 1 mm routed slot.
Run with KiCad Python. Source routing and footprints are never edited.
"""
from pathlib import Path
import json
import pcbnew as p
R=Path(__file__).resolve().parent
out=p.BOARD();out.SetCopperLayerCount(2);out.GetDesignSettings().SetBoardThickness(p.FromMM(.5))
def mm(x,y):return p.VECTOR2I(round(x*1e6),round(y*1e6))
sources=[]
netmap={}
for filename,prefix,dx,dy in [('ALPS_Adapter','A_',-10,-20.3),('Repair_Reference','R_',41.7,13.5)]:
 b=p.LoadBoard(str(R/(filename+'.kicad_pcb')));sources.append(b)
 assert abs(p.ToMM(b.GetDesignSettings().GetBoardThickness())-.5)<1e-6
 def net(name):
  key=prefix+name
  if key not in netmap:
   n=p.NETINFO_ITEM(out,key);out.Add(n);netmap[key]=n
  return netmap[key]
 for f in b.GetFootprints():
  g=p.Cast_to_FOOTPRINT(f.Duplicate(False));padnets=[q.GetNetname() for q in f.Pads()]
  g.SetReference(prefix+f.GetReference());g.Move(mm(dx,dy));out.Add(g)
  for q,name in zip(g.Pads(),padnets):
   if name:q.SetNet(net(name))
 for t in b.GetTracks():
  g=p.Cast_to_PCB_TRACK(t.Duplicate());g.Move(mm(dx,dy));out.Add(g);g.SetNet(net(t.GetNetname()))
 for z in b.Zones():
  g=p.Cast_to_ZONE(z.Duplicate(False));g.Move(mm(dx,dy));out.Add(g)
  if z.GetNetname():g.SetNet(net(z.GetNetname()))
 for d in b.GetDrawings():
  if d.GetLayer() not in [p.F_SilkS,p.B_SilkS]:continue
  g=d.Duplicate();g.Move(mm(dx,dy));out.Add(g)
def line(a,b):
 s=p.PCB_SHAPE(out);s.SetShape(p.SHAPE_T_SEGMENT);s.SetStart(mm(*a));s.SetEnd(mm(*b));s.SetLayer(p.Edge_Cuts);s.SetWidth(p.FromMM(.05));out.Add(s)
def arc(a,m,b):
 s=p.PCB_SHAPE(out);s.SetShape(p.SHAPE_T_ARC);s.SetArcGeometry(mm(*a),mm(*m),mm(*b));s.SetLayer(p.Edge_Cuts);s.SetWidth(p.FromMM(.05));out.Add(s)
outer=[(50,118.2),(94.176108,118.2),(94.176108,109.7),(101.7,109.7),(101.7,131.376108),(132.7,131.376108),(132.7,50),(70,50),(50,69.7)]
for a,b in zip(outer,outer[1:]+outer[:1]):line(a,b)
# Closed capsule, 1 mm wide, overall length 53.7 mm; tabs remain at both ends.
line((100.7,53.5),(100.7,106.2));arc((100.7,106.2),(101.2,106.7),(101.7,106.2))
line((101.7,106.2),(101.7,53.5));arc((101.7,53.5),(101.2,53),(100.7,53.5))
p.SaveBoard(str(R/'Order_Combined.kicad_pcb'),out)
report={'thickness_mm':.5,'size_mm':[82.7,81.376108],'routing_slot_width_mm':1,'routing_slot_overall_length_mm':53.7,'slot_radius_mm':.5,'tab_length_mm':3,'tab_count':2,'slot_bounds_mm':[100.7,53,101.7,106.7],'adapter_translation_mm':[-10,-20.3],'repair_translation_mm':[41.7,13.5],'outer_outline_mm':outer,'source_files':['ALPS_Adapter.kicad_pcb','Repair_Reference.kicad_pcb'],'note':'Two electrical designs, one mechanically connected blank. Cut tabs after manufacture; never use V-score across castellated edges.'}
(R/'reference/order-board.json').write_text(json.dumps(report,indent=2)+'\n')
print('Order_Combined.kicad_pcb: two designs, one connected 0.5 mm board; 1 mm slot; two 3 mm tabs.')
