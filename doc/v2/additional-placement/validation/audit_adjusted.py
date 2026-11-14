import json,hashlib
from pathlib import Path
from shapely.geometry import Polygon
from shapely.ops import unary_union
p=Path('/workspace/Cambridge_640A_v2_adjusted'); s=Path('/workspace/Cambridge_640A_v2_silkscreen')
a=json.loads((s/'native_geometry.json').read_text())['footprints']; b=json.loads((p/'native_geometry.json').read_text())['footprints']
assert set(a)==set(b)
changed=[]; errors=[]
for r in a:
 if any(a[r][k]!=b[r][k] for k in ['xy','angle','footprint']): changed.append(r)
 if a[r]['value']!=b[r]['value']: errors.append(['value',r])
 if sorted((x['number'],x['net']) for x in a[r]['pads'])!=sorted((x['number'],x['net']) for x in b[r]['pads']): errors.append(['nets',r])
shapes={r:unary_union([Polygon(poly) for poly in f['polys']]) for r,f in b.items()}
for r in changed:
 for t in b:
  if r!=t and shapes[r].intersection(shapes[t]).area>1e-6: errors.append(['courtyard',r,t])
assert (s/'640A_PowerAmp.kicad_pro').read_bytes()==(p/'640A_PowerAmp.kicad_pro').read_bytes()
assert set(changed)==set('C22 C17 R42 R31 R34 C42 R75 R77 R122 R123 C80'.split()),changed
out={'footprint_count':len(b),'physical_changes':sorted(changed),'values_and_pad_nets_preserved':not errors,'project_rules_and_exclusions_unchanged':True,'changed_courtyard_overlaps':[e for e in errors if e[0]=='courtyard'],'source_pcb_sha256':hashlib.sha256((s/'640A_PowerAmp.kicad_pcb').read_bytes()).hexdigest(),'errors':errors}
(p/'validation/independent_audit.json').write_text(json.dumps(out,indent=2)+'\n'); print(json.dumps(out,indent=2)); assert not errors
