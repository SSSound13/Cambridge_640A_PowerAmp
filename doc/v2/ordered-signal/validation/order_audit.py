from pathlib import Path
import json,hashlib
from shapely.geometry import Polygon,LineString
from shapely.ops import unary_union
s=Path('/workspace/Cambridge_640A_v2_adjusted');p=Path('/workspace/Cambridge_640A_v2_order_preview')
a=json.loads((s/'native_geometry.json').read_text())['footprints'];b=json.loads((p/'native_geometry.json').read_text())['footprints'];old=json.loads((s/'routed_geometry.json').read_text())['tracks'];new=json.loads((p/'routed_geometry.json').read_text())['tracks'];expected=set('R12 R13 R104 R105 R60 R61 R62 R63'.split());errors=[]
assert set(a)==set(b)
changed={r for r in a if any(a[r][k]!=b[r][k] for k in ['xy','angle','footprint'])};assert changed==expected
for r in a:
 assert a[r]['footprint']==b[r]['footprint'] and a[r]['value']==b[r]['value']
 assert [(q['number'],q['net']) for q in a[r]['pads']]==[(q['number'],q['net']) for q in b[r]['pads']]
sh={r:unary_union([Polygon(v) for v in x['polys']]) for r,x in b.items()}
for r in changed:
 for t in b:
  if t!=r and sh[r].intersection(sh[t]).area>1e-7:errors.append(['courtyard',r,t])
pairs={'R13':'R60','R12':'R61','R104':'R63','R105':'R62'}
for l,r in pairs.items():
 for u,v in zip(b[l]['pads'],b[r]['pads']):assert all(abs(v['xy'][i]-u['xy'][i]-[129.5,-1.25][i])<1e-6 for i in range(2))
 assert b[l]['angle']==b[r]['angle'] and b[l]['value']==b[r]['value']
assert {t['uuid'] for t in old if t['via']}=={t['uuid'] for t in new if t['via']}
for f in list(s.glob('*.kicad_sch'))+[s/'640A_PowerAmp.kicad_pro']:assert f.read_bytes()==(p/f.name).read_bytes()
for route in json.loads((p/'ordered_links.json').read_text()):
 rr,pn=route['from'].split('.');ss,qn=route['to'].split('.');u=next(q for q in b[rr]['pads'] if q['number']==pn);v=next(q for q in b[ss]['pads'] if q['number']==qn)
 assert any(t['net']==u['net'] and t['layer']=='F.Cu' and t['width']==.5 and {tuple(t['start']),tuple(t['end'])}=={tuple(u['xy']),tuple(v['xy'])} for t in new)
result={'changed_footprints':sorted(changed),'component_count':len(b),'pairs':pairs,'pair_translation_mm':[129.5,-1.25],'column_pitch_mm':10,'row_pitch_mm':2.75,'pad_pitch_mm':7.62,'manual_links_mm':2.38,'manual_width_mm':.5,'new_vias':0,'schemas_rules_and_exclusions_unchanged':True,'errors':errors};assert not errors
(p/'validation/order_audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
