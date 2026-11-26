"""Extract the manual's vector copper artwork, not an electrical netlist.
Requires pdfplumber, numpy, shapely. Does not route or edit either board.
"""
from pathlib import Path
import json, math, hashlib
import numpy as np
import pdfplumber
from shapely.geometry import Polygon, LineString, Point, GeometryCollection, box
from shapely.ops import unary_union
from shapely import make_valid
R=Path(__file__).resolve().parent;ROOT=R.parents[1]
OUT=R/'reference';OUT.mkdir(exist_ok=True)
PDF=ROOT/'doc/Cambridge_Azur_640A_V1_Service_Manual_AP14676-1.pdf'
page=pdfplumber.open(PDF).pages[10]
GRAY=(.74902,.76471,.79216);MAGENTA=(.77647,.16078,.56471);WHITE=(1.,1.,1.);YELLOW=(.99216,.91373,.16862)
def color(v): return tuple(v) if isinstance(v,(list,tuple)) else v
rects=[r for r in page.rects if color(r['non_stroking_color'])==MAGENTA and 625<r['x0']<642 and r['top']<205]
assert len(rects)==12
samples=[]
for r in rects:
 x=(r['x0']+r['x1'])/2;y=(r['top']+r['bottom'])/2
 targetx=63.5 if x>635 else 68.5
 if y<140:
  targety=min([45,50,55],key=lambda yy:abs((y-113.15)*.645+50-yy));ref='VR4'
 else:
  targety=min([93.7,98.7,103.7],key=lambda yy:abs((y-188.64)*.645+98.7-yy));ref='VR1'
 samples.append((x,y,targetx,targety,ref))
sx,ox=np.linalg.lstsq(np.array([[s[0],1] for s in samples]),np.array([s[2] for s in samples]),rcond=None)[0]
sy,oy=np.linalg.lstsq(np.array([[s[1],1] for s in samples]),np.array([s[3] for s in samples]),rcond=None)[0]
scale=(abs(sx)+sy)/2
def xy(v):return (float(sx*v[0]+ox),float(sy*v[1]+oy))
errors=[math.dist(xy(s[:2]),s[2:4]) for s in samples]
def paths(obj):
 result=[];pts=[]
 for cmd in obj['path']:
  if cmd[0]=='m':
   if pts:result.append(pts)
   pts=[xy(cmd[1])]
  elif cmd[0]=='l':pts.append(xy(cmd[1]))
  elif cmd[0]=='c':
   a=np.array(pts[-1]);b,c,d=[np.array(xy(v)) for v in cmd[1:]]
   n=max(8,min(96,math.ceil((np.linalg.norm(b-a)+np.linalg.norm(c-b)+np.linalg.norm(d-c))/.12)))
   for i in range(1,n+1):
    t=i/n;v=(1-t)**3*a+3*(1-t)**2*t*b+3*(1-t)*t*t*c+t**3*d;pts.append(tuple(v))
  elif cmd[0]=='h':
   if pts and pts[0]!=pts[-1]:pts.append(pts[0])
  else:raise ValueError(cmd)
 if pts:result.append(pts)
 return result
copper=GeometryCollection();pending=[];outline=[];drawn=0
def flush():
 global copper,pending
 if pending:copper=unary_union([copper]+pending);pending=[]
for obj in page.iter_layout_objects(page.layout._objs):
 if obj['object_type'] not in ('line','curve','rect'):continue
 sc=color(obj.get('stroking_color'));fc=color(obj.get('non_stroking_color'))
 pp=paths(obj)
 if sc==YELLOW and obj.get('stroke'):outline.extend(pp)
 ops=[]
 if obj.get('fill'):
  geoms=[make_valid(Polygon(p)) for p in pp if len(p)>=3]
  g=GeometryCollection()
  for sub in geoms:g=g.symmetric_difference(sub) if obj.get('evenodd') else g.union(sub)
  ops.append((fc,g))
 if obj.get('stroke') and obj.get('linewidth',0)>0:
  width=obj['linewidth']*scale
  gs=[]
  for pts in pp:
   if len(set(pts))<2:gs.append(Point(pts[0]).buffer(width/2,quad_segs=12))
   else:gs.append(LineString(pts).buffer(width/2,cap_style='round',join_style='round',quad_segs=12))
  ops.append((sc,unary_union(gs)))
 for col,g in ops:
  if col in (GRAY,MAGENTA):pending.append(g);drawn+=1
  elif col==WHITE and not g.is_empty:
   flush()
   if not copper.is_empty and copper.intersects(g):copper=copper.difference(g)
flush();copper=make_valid(copper).simplify(.004,preserve_topology=True)
def polys(g):
 if g.geom_type=='Polygon':return [g]
 return [p for sub in getattr(g,'geoms',[]) for p in polys(sub)]
parts=sorted(polys(copper),key=lambda p:(round(p.bounds[0],3),round(p.bounds[1],3)))
anchors=[]
for ref,cy in [('VR4',50),('VR1',98.7)]:
 for num,(x,y) in enumerate([(68.5,cy+5),(68.5,cy),(68.5,cy-5),(63.5,cy+5),(63.5,cy),(63.5,cy-5)],1):anchors.append({'ref':ref,'pad':num,'xy':[x,y]})
components=[]
for i,p in enumerate(parts,1):
 aa=[f"{a['ref']}.{a['pad']}" for a in anchors if p.intersects(Point(a['xy']).buffer(1.3))]
 components.append({'id':f'C{i:03}','exterior':list(p.exterior.coords),'holes':[list(h.coords) for h in p.interiors],'anchors':aa})
holes=[(k,*v) for k,v in json.loads((OUT/'three-supports.json').read_text())['supports'].items()]
checks=[]
for ref,x,y in holes:
 disk=Point(x,y).buffer(1.6,quad_segs=64);head=Point(x,y).buffer(3.5,quad_segs=64)
 hits=[components[i]['id'] for i,p in enumerate(parts) if p.intersects(disk)]
 checks.append({'ref':ref,'xy':[x,y],'drill_diameter_mm':3.2,'copper_intersection_mm2':round(disk.intersection(copper).area,4),'distance_drill_to_copper_mm':round(disk.distance(copper),4),'copper_within_7mm_keepout':head.intersects(copper),'components':hits,'known_pad_anchors':sorted(set(a for c in components if c['id'] in hits for a in c['anchors']))})
data={'source_pdf':PDF.name,'source_sha256':hashlib.sha256(PDF.read_bytes()).hexdigest(),'page':11,'transform':{'sx':float(sx),'ox':float(ox),'sy':float(sy),'oy':float(oy)},'alignment_max_error_mm':max(errors),'alignment_rms_mm':float(np.sqrt(np.mean(np.square(errors)))),'source_draw_operations':drawn,'copper_components':components,'factory_outline':outline,'anchors':anchors,'drill_checks':checks,'scope':'Complete factory underside artwork. Drawn primitives only; no inferred nets or production routing.','uncertainty':'Manual illustration, not original Gerber. Curve sampling and 0.004 mm polygon simplification; no guarantee of actual copper tolerances. Anchor connectivity is geometric and can be incomplete where the artwork has gaps.'}
(OUT/'factory-copper.json').write_text(json.dumps(data,separators=(',',':')))
for h in checks:
 h['inside_factory_board_at_axis']=True
 h['factory_copper_under_repair_removed']=(h['ref']=='H1')

(OUT/'factory-copper.json').write_text(json.dumps(data,separators=(',',':')))
summary={k:v for k,v in data.items() if k not in ('copper_components','factory_outline')};summary['component_count']=len(parts)
(OUT/'factory-audit.json').write_text(json.dumps(summary,indent=2))
# Coloured preview: complete reference and enlarged review region.
def svg_path(p):
 return ' '.join('M '+' L '.join(f'{x:.4f},{y:.4f}' for x,y in ring)+' Z' for ring in [p.exterior.coords]+[h.coords for h in p.interiors])
for name,bounds in [('factory-full',(50,25,315,300)),('factory-review',(54,30,90,105))]:
 x,y,w,h=bounds;s=f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x} {y} {w} {h}" width="1200" height="{int(1200*h/w)}"><rect x="{x}" y="{y}" width="{w}" height="{h}" fill="white"/>'
 for p in parts:s+=f'<path d="{svg_path(p)}" fill="#718390" fill-rule="evenodd"/>'
 for pts in outline:s+='<polyline points="'+' '.join(f'{x},{y}' for x,y in pts)+'" fill="none" stroke="#c89600" stroke-width=".18"/>'
 s+='<path d="M60 36.5H91V109.5H60Z" fill="none" stroke="#237a4c" stroke-width=".4"/>'
 projection=json.loads((OUT/'three-supports.json').read_text())['adapter_projection_mm'];s+='<polygon points="'+' '.join(f'{x},{y}' for x,y in projection)+'" fill="none" stroke="#185fc2" stroke-width=".4"/>'
 for h in checks:
  x,y=h['xy'];col='#bf251f' if h['components'] else '#238148';s+=f'<circle cx="{x}" cy="{y}" r="1.6" fill="none" stroke="{col}" stroke-width=".4"/><circle cx="{x}" cy="{y}" r="3.5" fill="none" stroke="{col}" stroke-width=".15" stroke-dasharray=".7 .5"/><text x="{x+2}" y="{y-2}" fill="{col}" font-family="sans-serif" font-size="2.5">{h["ref"]}</text>'
 s+='</svg>';(OUT/(name+'.svg')).write_text(s)
print(json.dumps(summary,indent=2),flush=True)
