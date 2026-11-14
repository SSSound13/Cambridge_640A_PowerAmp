import pcbnew,json
from pathlib import Path
src=Path('/workspace/Cambridge_640A_v2_symmetric');r=Path('/workspace/Cambridge_640A_v2_reviewed')
b=pcbnew.LoadBoard(str(src/'640A_PowerAmp.kicad_pcb'));keep=[b]+list(b.GetTracks())+list(b.GetFootprints())+list(b.Zones())
def key(n,l,w,a,c):return(n,l,round(w,6),tuple(sorted((tuple(round(v,6) for v in a),tuple(round(v,6) for v in c)))))
old=sum([json.load(open(src/f))['routes'] for f in ['master_routes.json','boundary_routes.json']],[])
keys={key(t['net'],p['layer'],t['width'],a,c) for t in old for p in t['paths'] for a,c in zip(p['points'],p['points'][1:])}
removed=0
for t in list(b.GetTracks()):
 if isinstance(t,pcbnew.PCB_VIA):continue
 a=[pcbnew.ToMM(t.GetStart().x),pcbnew.ToMM(t.GetStart().y)];c=[pcbnew.ToMM(t.GetEnd().x),pcbnew.ToMM(t.GetEnd().y)]
 if key(t.GetNetname(),t.GetLayerName(),pcbnew.ToMM(t.GetWidth()),a,c) in keys:b.Remove(t);removed+=1
added=0
for f in ['master_routes.json','boundary_routes.json']:
 for route in json.load(open(r/f))['routes']:
  for p in route['paths']:
   for a,c in zip(p['points'],p['points'][1:]):
    if a==c:continue
    t=pcbnew.PCB_TRACK(b);t.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(a[0]),pcbnew.FromMM(a[1])));t.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(c[0]),pcbnew.FromMM(c[1])));t.SetWidth(pcbnew.FromMM(route['width']));t.SetLayer(pcbnew.F_Cu if p['layer']=='F.Cu' else pcbnew.B_Cu);t.SetNet(b.FindNet(route['net']));t.SetLocked(f=='master_routes.json');b.Add(t);keep.append(t);added+=1
b.BuildConnectivity();filler=pcbnew.ZONE_FILLER(b);filler.Fill(b.Zones());pcbnew.SaveBoard(str(r/'640A_PowerAmp.kicad_pcb'),b);print('removed',removed,'added',added)
