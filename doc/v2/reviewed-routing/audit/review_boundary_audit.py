import json,re,csv,math
from pathlib import Path
from shapely.geometry import LineString,Point
from shapely.ops import unary_union
from collections import defaultdict
r=Path('/workspace/Cambridge_640A_v2_reviewed');m=json.load(open(r/'master_routes.json'))['routes'];ad=json.load(open(r/'boundary_routes.json'))['routes'];scope=json.load(open(r/'symmetry_scope.json'));side={ref:'L' for ref in scope['pairs']};side.update({ref:'R' for ref in scope['pairs'].values()});groups=defaultdict(list)
for i,t in enumerate(m):
 for p in t['paths']:groups[(t['net'],'L' if i%2==0 else 'R')].append(LineString(p['points']))
groups={k:unary_union(v) for k,v in groups.items()};out=[];unexpected=[]
def classify(item,net):
 match=re.search(r' of (\w+)$',item['description'])
 if match:return ('matched_'+side[match[1]]) if match[1] in side else 'fixed_other'
 pt=Point(item['pos']['x'],item['pos']['y'])
 for ch in ['L','R']:
  if (net,ch) in groups and groups[(net,ch)].distance(pt)<.001:return 'matched_'+ch
 return 'existing_external_copper'
for boundary_index,t in enumerate(ad,1):
 a,b=t['endpoints'];ca,cb=[classify(i,t['net']) for i in [a,b]]
 if ca==cb and ca.startswith('matched_'):unexpected.append(t['connection'])
 out.append({'connection':boundary_index,'net':t['net'],'width_mm':t['width'],'endpoint_1':a['description'],'endpoint_2':b['description'],'endpoint_1_class':ca,'endpoint_2_class':cb,'length_mm':round(sum(LineString(p['points']).length for p in t['paths']),4),'vias':len(t['vias'])})
with open(r/'boundary_connections.csv','w') as f:
 w=csv.DictWriter(f,fieldnames=list(out[0]));w.writeheader();w.writerows(out)
report={'connections':len(out),'unexplained_same_channel_master_to_master':unexpected,'rows':out};json.dump(report,open(r/'validation/boundary_audit.json','w'),ensure_ascii=False,indent=2);print('Adapters',len(out),'unexpected',unexpected)
assert not unexpected
