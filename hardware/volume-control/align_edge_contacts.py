from pathlib import Path
import json,pcbnew as p
r=Path(__file__).resolve().parent;b=p.LoadBoard(str(r/'Repair_Reference.kicad_pcb'));fs={f.GetReference():f for f in b.GetFootprints()}
positions={'J1':(91,101.70494),'J2':(91,86.236944),'J3':(91,61.315669),'J4':(91,53.606969),'J5':(65.998582,109.5),'J6':(91,48.411463)}
if 'J6' not in fs:
 clone=p.Cast_to_FOOTPRINT(fs['J5'].Duplicate(False));clone.SetReference('J6');clone.SetValue('AGND_BAL_FACTORY');b.Add(clone);fs['J6']=clone
for ref,(x,y) in positions.items():
 fs[ref].SetPosition(p.VECTOR2I(p.FromMM(x),p.FromMM(y)));fs[ref].SetOrientationDegrees(90 if ref=='J5' else 0)
labels={'R IN':('J1',-4,1.5),'L IN':('J2',-4,1.5),'R OUT':('J3',-4,1.5),'L OUT':('J4',-4,1.5),'AGND':('J5',4,-1.5)}
for d in b.GetDrawings():
 if not isinstance(d,p.PCB_TEXT):continue
 t=d.GetText()
 if t in positions:
  x,y=positions[t];d.SetPosition(p.VECTOR2I(p.FromMM(x-4 if t!='J5' else x+4),p.FromMM(y-1.5)))
 elif t in labels:
  ref,dx,dy=labels[t];x,y=positions[ref];d.SetPosition(p.VECTOR2I(p.FromMM(x+dx),p.FromMM(y+dy)))
if not any(isinstance(d,p.PCB_TEXT) and d.GetText()=='J6 AGND' for d in b.GetDrawings()):
 d=p.PCB_TEXT(b);d.SetText('J6 AGND');d.SetPosition(p.VECTOR2I(p.FromMM(86),p.FromMM(46.7)));d.SetTextSize(p.VECTOR2I(p.FromMM(.7),p.FromMM(.7)));d.SetTextThickness(p.FromMM(.12));d.SetLayer(p.F_SilkS);b.Add(d)
p.SaveBoard(str(r/'Repair_Reference.kicad_pcb'),b)
report={'manual_pages':[8,10,11],'method':'Centre of factory copper intersection with actual repair board edge. Coordinates approximate artwork registration; verify physical board with 1:1 template.','contacts':[],'jumpers_from_page10_mm':[[[74.843696,60.013984],[64.685184,60.013984]],[[75.606496,76.647963],[65.447405,76.647963]]],'routing':'Existing tracks untouched; relocated edge contacts need electrical routing review.'}
components=['C018','C030','C026','C017','C005','C003'];evidence=['VR1.3','VR1.6 via original top-side jumper','VR4.5 via original top-side jumper','VR4.2','VR1.1 / VR1.4 ground','VR4.3 / VR4.4 ground']
for (ref,xy),component,source in zip(positions.items(),components,evidence):report['contacts'].append({'reference':ref,'xy_mm':xy,'net':next(iter(fs[ref].Pads())).GetNetname(),'factory_component':component,'source':source})
(r/'reference/edge-solder-alignment.json').write_text(json.dumps(report,indent=2))
print('Aligned six edge solder contacts; copper tracks untouched')

