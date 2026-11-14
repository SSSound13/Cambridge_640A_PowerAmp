import pcbnew,json,math,hashlib
from pathlib import Path
r=Path('/workspace/Cambridge_640A_v2_reviewed');b=pcbnew.LoadBoard(str(r/'640A_PowerAmp.kicad_pcb'));fplist=list(b.GetFootprints());tracks=list(b.GetTracks());keep=[b]+fplist+tracks;out=[];fps={};viol=[]
for f in fplist:
 pads=list(f.Pads());keep+=pads
 fps[f.GetReference()]={'xy':[pcbnew.ToMM(f.GetPosition().x),pcbnew.ToMM(f.GetPosition().y)],'angle':f.GetOrientationDegrees(),'footprint':f.GetFPIDAsString(),'pads':[{'number':p.GetNumber(),'net':p.GetNetname(),'xy':[pcbnew.ToMM(p.GetPosition().x),pcbnew.ToMM(p.GetPosition().y)],'size':[pcbnew.ToMM(p.GetSize().x),pcbnew.ToMM(p.GetSize().y)],'drill':[pcbnew.ToMM(p.GetDrillSize().x),pcbnew.ToMM(p.GetDrillSize().y)]} for p in pads]}
for t in tracks:
 via=isinstance(t,pcbnew.PCB_VIA);out.append({'uuid':t.m_Uuid.AsString(),'start':[pcbnew.ToMM(t.GetStart().x),pcbnew.ToMM(t.GetStart().y)],'end':[pcbnew.ToMM(t.GetEnd().x),pcbnew.ToMM(t.GetEnd().y)],'width':pcbnew.ToMM(t.GetWidth(pcbnew.F_Cu) if via else t.GetWidth()),'net':t.GetNetname(),'layer':t.GetLayerName(),'via':via,'drill':pcbnew.ToMM(t.GetDrillValue()) if via else None,'locked':t.IsLocked()})
old=json.load(open('/workspace/Cambridge_640A_v2_placement_plan/native_geometry.json'))['footprints']
for ref,original in old.items():
 now=fps[ref]
 for key in ['xy','angle','footprint']:
  if now[key]!=original[key]:viol.append([ref,key])
 for p in now['pads']:
  op=next(q for q in original['pads'] if p['number']==q['number'])
  for key in ['net','xy','size','drill']:
   if p[key]!=op[key]:viol.append([ref,p['number'],key])
json.dump({'footprints':fps,'tracks':out},open(r/'routed_geometry.json','w'),indent=2)
json.dump({'footprints':len(fps),'tracks':sum(not t['via'] for t in out),'vias':sum(t['via'] for t in out),'placement_or_net_changes':viol},open(r/'validation/routing_invariants.json','w'),indent=2)
print('audit',len(fps),len(out),'invariant errors',viol)
