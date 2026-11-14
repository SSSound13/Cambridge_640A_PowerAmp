import json,math,copy
from pathlib import Path
from shapely.geometry import LineString,Point,Polygon,box
from shapely.ops import unary_union
from shapely.affinity import translate
from shapely.prepared import prep
r=Path('/workspace/Cambridge_640A_v2_reviewed');src=Path('/workspace/Cambridge_640A_v2_symmetric')
m=json.load(open(src/'master_routes.json'));b=json.load(open(src/'boundary_routes.json'));g=json.load(open(src/'routed_geometry.json'));pads=json.load(open(src/'pad_shapes.json'))
obs=[]
for p in pads:obs.append((Polygon(p['polygon']),p['net'],p['layer']))
for t in g['tracks']:obs.append((Point(t['start']).buffer(t['width']/2) if t['via'] else LineString([t['start'],t['end']]).buffer(t['width']/2),t['net'],None if t['via'] else t['layer']))
# Preserve every junction where another route starts/ends or original copper attaches.
def key(n,l,w,a,c):return(n,l,round(w,6),tuple(sorted((tuple(round(v,6) for v in a),tuple(round(v,6) for v in c)))))
keys={key(t['net'],p['layer'],t['width'],a,c) for t in m['routes']+b['routes'] for p in t['paths'] for a,c in zip(p['points'],p['points'][1:])}
anchors=[]
for t in m['routes']+b['routes']:
 for p in t['paths']:
  anchors.extend((t['net'],p['layer'],x) for x in [p['points'][0],p['points'][-1]])
for t in g['tracks']:
 if t['via'] or key(t['net'],t['layer'],t['width'],t['start'],t['end']) not in keys:
  anchors.extend((t['net'],None if t['via'] else t['layer'],x) for x in [t['start'],t['end']])
def candidates(a,c):
 dx=c[0]-a[0];dy=c[1]-a[1];sx=1 if dx>=0 else -1;sy=1 if dy>=0 else -1;v=min(abs(dx),abs(dy))
 if min(abs(dx),abs(dy),abs(abs(dx)-abs(dy)))<1e-6:yield [a,c]
 for mid in [(a[0]+sx*v,a[1]+sy*v),(c[0]-sx*v,c[1]-sy*v)]:
  if math.dist(a,mid)>1e-6 and math.dist(mid,c)>1e-6:yield [a,mid,c]
def clean(t,p,other=None):
 pts=p['points'];line=LineString(pts);near=box(*line.buffer(3).bounds);shapes=[]
 for k,net in enumerate([t['net'],other['net']] if other else [t['net']]):
  for geom,n,l in obs:
   if n==net or l not in (None,p['layer']):continue
   q=translate(geom,xoff=-98.9558*k) if k else geom
   if near.intersects(q):shapes.append(q)
 forbidden=prep(unary_union(shapes).buffer(t['width']/2+.200005))
 positions={0.,line.length}
 for k,net in enumerate([t['net'],other['net']] if other else [t['net']]):
  for n,l,xy in anchors:
   if n!=net or l not in (None,p['layer']):continue
   q=Point(xy[0]-98.9558*k,xy[1])
   if line.distance(q)<.000003:positions.add(line.project(q))
 # Include original vertices and all electrical branch points.
 verts=[];d=0
 for a,c in zip(pts,pts[1:]):verts.append((d,a));d+=math.dist(a,c)
 verts.append((d,pts[-1]));verts += [(d,list(line.interpolate(d).coords)[0]) for d in positions]
 unique={round(d,6):(d,list(x)) for d,x in verts};verts=sorted(unique.values());cuts=sorted(set(min(range(len(verts)),key=lambda i:abs(verts[i][0]-d)) for d in positions));out=[]
 for lo,hi in zip(cuts,cuts[1:]):
  v=[x for _,x in verts[lo:hi+1]];cost=[float('inf')]*len(v);paths=[None]*len(v);cost[0]=0;paths[0]=[v[0]]
  for j in range(1,len(v)):
   for i in range(j):
    opts=list(candidates(v[i],v[j]));
    if j==i+1:opts.append([v[i],v[j]])
    for q in opts:
     score=cost[i]+LineString(q).length+.35*(len(q)-1)
     if score>=cost[j]-1e-8:continue
     if not (j==i+1 and len(q)==2) and forbidden.intersects(LineString(q)):continue
     cost[j]=score;paths[j]=paths[i]+q[1:]
  out+=paths[-1] if not out else paths[-1][1:]
 return [[round(x,6),round(y,6)] for x,y in out]
stats=[]
for i in range(0,len(m['routes']),2):
 a,c=m['routes'][i:i+2]
 for p,q in zip(a['paths'],c['paths']):
  old=p['points'];new=clean(a,p,c);p['points']=new;q['points']=[[round(x+98.9558,6),y] for x,y in new]
  obs.extend([(LineString(p['points']).buffer(a['width']/2),a['net'],p['layer']),(LineString(q['points']).buffer(c['width']/2),c['net'],q['layer'])])
  stats.append({'pair':a['pair'],'net':a['net'],'from':a['from'],'to':a['to'],'segments_before':len(old)-1,'segments_after':len(new)-1,'length_before':LineString(old).length,'length_after':LineString(new).length})
 print('pair',i//2,flush=True)
# Boundary routes use the same simplifier, preserving the recorded attachment points.
for i,a in enumerate(b['routes']):
 for p in a['paths']:
  old=p['points'];p['points']=clean(a,p);obs.append((LineString(p['points']).buffer(a['width']/2),a['net'],p['layer']));stats.append({'boundary':i,'net':a['net'],'segments_before':len(old)-1,'segments_after':len(p['points'])-1,'length_before':LineString(old).length,'length_after':LineString(p['points']).length})
json.dump(m,open(r/'master_routes.json','w'),indent=2);json.dump(b,open(r/'boundary_routes.json','w'),indent=2);json.dump(stats,open(r/'cleanup_metrics.json','w'),indent=2)
print('TOTAL',sum(s['segments_before'] for s in stats),sum(s['segments_after'] for s in stats))
