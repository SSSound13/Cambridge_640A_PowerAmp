import json,math
from pathlib import Path
from collections import defaultdict,Counter
from shapely.geometry import LineString,Point
from shapely.ops import unary_union
r=Path('/workspace/Cambridge_640A_v2_reviewed');m=json.load(open(r/'master_routes.json'));scope=json.load(open(r/'symmetry_scope.json'));g=json.load(open(r/'routed_geometry.json'));routes=m['routes'];actual=g['tracks'];errors=[];native=defaultdict(list)
for t in actual:
 if not t['via']:native[(t['net'],t['layer'],round(t['width'],6))].append(LineString([t['start'],t['end']]))
coverage={k:unary_union(v).buffer(.000003) for k,v in native.items()}
for i in range(0,len(routes),2):
 a,b=routes[i:i+2]
 for key in ['width','via_diameter','via_drill']:
  if a[key]!=b[key]:errors.append([i//2,key])
 for p,q in zip(a['paths'],b['paths']):
  if p['layer']!=q['layer'] or len(p['points'])!=len(q['points']):errors.append([i//2,'layer/points'])
  for u,v in zip(p['points'],q['points']):
   if max(abs(v[0]-u[0]-98.9558),abs(v[1]-u[1]))>.000001:errors.append([i//2,'translation'])
 for a in [a,b]:
  for p in a['paths']:
   geom=coverage.get((a['net'],p['layer'],round(a['width'],6)))
   if geom is None or LineString(p['points']).difference(geom).length>.00001:errors.append([a['pair'],a['net'],'missing or changed native track'])
  for xy in a['vias']:
   if not any(t['via'] and t['net']==a['net'] and math.dist(t['start'],xy)<.000002 and abs(t['width']-a['via_diameter'])<.000001 and abs(t.get('drill',a['via_drill'])-a['via_drill'])<.000001 for t in actual):errors.append([a['pair'],a['net'],'missing or changed via'])
# Check that every multi-terminal net in the matched component set has one connected master tree.
by=defaultdict(set)
for ref in scope['pairs']:
 for p in g['footprints'][ref]['pads']:by[p['net']].add(ref+'.'+p['number'])
for net,nodes in by.items():
 if len(nodes)<2:continue
 connected={next(iter(nodes))}
 while True:
  prev=len(connected)
  for t in routes[::2]:
   if t['net']==net and (t['from'] in connected or t['to'] in connected):connected|={t['from'],t['to']}
  if len(connected)==prev:break
 if connected!=nodes:errors.append([net,'incomplete master tree',sorted(nodes-connected)])
report={'matched_component_pairs':len(scope['pairs']),'matched_terminals_per_channel':sum(len(n) for n in by.values()),'local_nets_per_channel':len(by),'paired_connections':len(routes)//2,'paired_connections_by_width_mm':dict(Counter(str(t['width']) for t in routes[::2])),'native_track_centerline_tolerance_mm':.000003,'pair_translation_mm':[98.9558,0],'failed_routes':m['failed'],'errors':errors}
json.dump(report,open(r/'validation/master_symmetry.json','w'),indent=2);print(json.dumps(report));assert not errors and not m['failed']
