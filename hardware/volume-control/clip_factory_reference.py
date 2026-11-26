"""Crop manual reference graphics, never board copper. Requires Shapely."""
from pathlib import Path
import json
from shapely.geometry import Polygon,LineString,box
R=Path(__file__).resolve().parent
data=json.loads((R/'reference/factory-copper.json').read_text())
mech=json.loads((R/'reference/three-supports.json').read_text())
pts=mech['repair_outline_mm']+mech['adapter_projection_mm']
bounds=[min(p[0] for p in pts)-5,min(p[1] for p in pts)-5,max(p[0] for p in pts)+5,max(p[1] for p in pts)+50]
window=box(*bounds);components=[];outlines=[]
for c in data['copper_components']:
 g=Polygon(c['exterior'],c['holes']).intersection(window)
 for part in ([g] if g.geom_type=='Polygon' else getattr(g,'geoms',[])):
  if part.is_empty or part.geom_type!='Polygon':continue
  item=dict(c);item['exterior']=list(part.exterior.coords);item['holes']=[list(h.coords) for h in part.interiors];components.append(item)
for pts in data['factory_outline']:
 g=LineString(pts).intersection(window)
 for part in ([g] if g.geom_type=='LineString' else getattr(g,'geoms',[])):
  if part.is_empty or part.geom_type!='LineString':continue
  outlines.append(list(part.coords))
data.update(copper_components=components,factory_outline=outlines,reference_window_mm=bounds,reference_window_note='50 mm below the lowest board contour; 5 mm context at top and sides. Reference graphics only; original manual unchanged.')
(R/'reference/factory-copper-window.json').write_text(json.dumps(data,separators=(',',':')))
print('Reference window:',bounds,'polygons:',len(components))
