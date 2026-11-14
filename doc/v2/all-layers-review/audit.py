import json,math,collections,hashlib
from pathlib import Path
s=Path('/workspace/Cambridge_640A_v2_ordered');p=Path('/workspace/Cambridge_640A_v2_all_layers');a=json.loads((s/'all_layers_review/geometry.json').read_text());b=json.loads((p/'all_layers_review/geometry.json').read_text());by={t['uuid']:t for t in a['tracks']};now={t['uuid']:t for t in b['tracks']};assert set(by)==set(now);changed=[u for u in by if by[u]!=now[u]]
assert a['pads']==b['pads'];assert a['net_ties']==b['net_ties'];assert a['zones']==b['zones']
assert all(by[u]==now[u] for u in by if by[u]['via'] or by[u]['layer'] in ['In1.Cu','In2.Cu'] or by[u]['net']=='PGND')
for f in list(s.glob('*.kicad_sch'))+[s/'640A_PowerAmp.kicad_pro']:assert f.read_bytes()==(p/f.name).read_bytes()
summary={}
for layer in ['F.Cu','In1.Cu','In2.Cu','B.Cu']:
 ts=[t for t in b['tracks'] if t['layer']==layer and not t['via']];summary[layer]={'segments':len(ts),'total_length_mm':round(sum(math.dist(t['start'],t['end']) for t in ts),3),'widths_mm':sorted({t['width'] for t in ts})}
drc=json.loads((p/'all_layers_review/final_drc.json').read_text());assert not drc['violations'] and not drc['unconnected_items'] and not drc['schematic_parity'];ex=json.loads((s/'all_layers_review/drc_including_exclusions.json').read_text());assert all(v.get('excluded') and v['type']=='courtyards_overlap' for v in ex['violations'])
out={'layer_summary':summary,'track_count':len(by),'changed_tracks':len(changed),'change_details':[{'before':by[u],'after':now[u]} for u in changed],'inner_tracks_unchanged':True,'filled_inner_planes_unchanged':True,'pads_and_net_ties_unchanged':True,'pgnd_tracks_unchanged':True,'vias_unchanged':True,'rules_and_schematics_unchanged':True,'active_drc_violations':0,'inherited_excluded_courtyard_violations':len(ex['violations']),'errors':[]};(p/'all_layers_review/final_audit.json').write_text(json.dumps(out,indent=2));print('modified',len(changed),'excluded courtyard',len(ex['violations']),'layers',summary)
