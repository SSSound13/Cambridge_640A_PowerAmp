"""Bounded octilinear routing proposal. Requires Shapely; KiCad DRC remains authoritative.
No vias or neckdowns. Each pad-to-pad branch has <=3 segments, or <=4 fallback.
"""
from pathlib import Path
import json,math,itertools
from shapely.geometry import Polygon,Point,LineString,box
from shapely.affinity import rotate,translate
from shapely.ops import unary_union
R=Path(__file__).resolve().parent
data=json.loads((R/'reference/routing-input.json').read_text());mech=json.loads((R/'reference/three-supports.json').read_text())
dirs=[(1,0),(0,1),(1,1),(1,-1)]
def clean(pts):
 out=[]
 for q in pts:
  q=(round(q[0],6),round(q[1],6))
  if out and math.dist(q,out[-1])<.00001:continue
  while len(out)>1 and abs((out[-1][0]-out[-2][0])*(q[1]-out[-1][1])-(out[-1][1]-out[-2][1])*(q[0]-out[-1][0]))<.00001:out.pop()
  out.append(q)
 return out
def two(a,b):
 for u,v in itertools.product(dirs,repeat=2):
  den=u[0]*v[1]-u[1]*v[0]
  if not den:continue
  t=((b[0]-a[0])*v[1]-(b[1]-a[1])*v[0])/den
  yield clean([a,(a[0]+t*u[0],a[1]+t*u[1]),b])
def shape(q):
 w,h=q['size']
 if q['npth']:return Point(q['xy']).buffer(3.5,quad_segs=24)
 if q['shape']==0:return Point(q['xy']).buffer(w/2,quad_segs=24)
 # Bounding rectangle conservatively encloses roundrect/oval pads.
 return translate(rotate(box(-w/2,-h/2,w/2,h/2),q['angle'],origin=(0,0)),*q['xy'])
result={'width_mm':1,'clearance_mm':.25,'edge_clearance_mm':.5,'max_segments':4,'preferred_segments':3,'vias':0,'boards':{}}
for name,d in data.items():
 pads=d['pads'];shapes={q['id']:shape(q) for q in pads};outline=mech['adapter_outline_mm'] if name=='ALPS_Adapter' else [(60,36.5),(91,36.5),(91,109.5),(60,109.5)]
 board=Polygon(outline);inner=board.buffer(-1.001);routes=[];parent={q['id']:q['id'] for q in pads}
 def root(i):
  while parent[i]!=i:i=parent[i]
  return i
 pairs=sorted([(math.dist(a['xy'],b['xy']),a,b) for a,b in itertools.combinations(pads,2) if a['net'] and a['net']==b['net']],key=lambda x:x[0])
 for limit in [3,4]:
  for dist,a,b in pairs:
   if root(a['id'])==root(b['id']):continue
   def landing(q):
    q=dict(q);x,y=q['xy']
    if name=='Repair_Reference':
     if abs(x-91)<.001:x=89.99
     if abs(y-109.5)<.001:y=108.49
    q['xy']=[x,y];return q
   a,b=landing(a),landing(b)
   best=None
   for layer in ['F.Cu','B.Cu']:
    if layer not in a['layers'] or layer not in b['layers']:continue
    obstacles=[]
    for q in pads:
     if q['net']==a['net'] and not q['npth']:continue
     if layer not in q['layers'] and not q['npth']:continue
     obstacles.append(shapes[q['id']].buffer(.751 if not q['npth'] else .501))
    for rt in routes:
     if rt['layer']==layer and rt['net']!=a['net']:
      clearance=1 if ('MOTOR' in rt['net'])!=('MOTOR' in a['net']) else .25
      obstacles.append(LineString(rt['points']).buffer(1+clearance+.001))
    blocked=unary_union(obstacles)
    allowed=inner
    for endpoint in [a,b]:
     # Castellated pads intentionally sit on Edge.Cuts: permit the final approach
     # inside their pad area instead of imposing the ordinary copper-edge gap.
     if board.boundary.distance(Point(endpoint['xy']))<.001:
      allowed=allowed.union(board.intersection(shapes[endpoint['id']]))
    def valid(pts):
     if len(pts)<2:return False
     line=LineString(pts)
     return allowed.covers(line) and not blocked.intersects(line)
    def candidates(start,end,n):
     yield from two(start,end)
     for u in dirs:
      for step in range(-140,141):
       if not step:continue
       mid=(start[0]+u[0]*step*.5,start[1]+u[1]*step*.5)
       if not valid([start,mid]):continue
       for tail in two(mid,end):yield clean([start]+tail)
    # Four segments are attempted only after every three-segment pair attempt.
    sources=[(a['xy'],[])] if limit==3 else [( (a['xy'][0]+u[0]*t,a['xy'][1]+u[1]*t),[a['xy']]) for u in dirs for t in [-8,-4,-2,2,4,8]]
    for start,prefix in sources:
     if prefix and not valid(prefix+[start]):continue
     for tail in candidates(start,b['xy'],limit):
      pts=clean(prefix+tail)
      if len(pts)-1>limit:continue
      length=LineString(pts).length
      if best and length>=best[0]:continue
      if valid(pts):best=(length,pts,layer)
    # Prefer the front layer when it provides a short route.
   if best:
    routes.append(dict(net=a['net'],start=a['id'],end=b['id'],points=best[1],layer=best[2],segments=len(best[1])-1,length_mm=round(best[0],3)));parent[root(a['id'])]=root(b['id'])
  print(name,'segment limit',limit,'branches',len(routes),flush=True)
 missing=[]
 for net in sorted(set(q['net'] for q in pads if q['net'])):
  groups={}
  for q in pads:
   if q['net']==net:groups.setdefault(root(q['id']),[]).append(q['id'])
  if len(groups)>1:missing.append({'net':net,'disconnected_groups':list(groups.values())})
 result['boards'][name]={'removed_old_tracks':d['old_track_count'],'routes':routes,'unrouted_nets':missing}
(R/'reference/routing-attempt.json').write_text(json.dumps(result,indent=2))
