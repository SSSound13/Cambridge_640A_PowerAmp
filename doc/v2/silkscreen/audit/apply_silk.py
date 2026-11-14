import pcbnew,json,math
from pathlib import Path
r=Path('/workspace/Cambridge_640A_v2_silkscreen');src=Path('/workspace/Cambridge_640A_v2_reviewed');b=pcbnew.LoadBoard(str(src/'640A_PowerAmp.kicad_pcb'));fs=list(b.GetFootprints());keep=[b]+fs;by={f.GetReference():f for f in fs};data=json.load(open(r/'silkscreen_placement.json'));changes=[]
for item in data['labels']:
 t=by[item['ref']].Reference();keep.append(t);t.SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(1),pcbnew.FromMM(1)));t.SetTextThickness(pcbnew.FromMM(.15));t.SetTextAngle(pcbnew.EDA_ANGLE(item.get('angle',0),pcbnew.DEGREES_T));t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER);t.SetVertJustify(pcbnew.GR_TEXT_V_ALIGN_CENTER);t.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(item['xy'][0]),pcbnew.FromMM(item['xy'][1])))
# Move both strokes of C29's '+' together, retaining a complete polarity sign.
gs=list(by['C29'].GraphicalItems());keep+=gs
for g in gs:
 if g.GetLayer()!=pcbnew.F_SilkS or not isinstance(g,pcbnew.PCB_SHAPE) or g.GetShape()!=pcbnew.SHAPE_T_SEGMENT:continue
 cx=pcbnew.ToMM(g.GetStart().x+g.GetEnd().x)/2;cy=pcbnew.ToMM(g.GetStart().y+g.GetEnd().y)/2
 if math.hypot(cx-183.0406,cy-97.62346)<.01:g.Move(pcbnew.VECTOR2I(pcbnew.FromMM(-2),0));changes.append(g.m_Uuid.AsString())
for lead in data.get('leaders',[]):
 for a,c in zip(lead['points'],lead['points'][1:]):
  g=pcbnew.PCB_SHAPE(b);g.SetShape(pcbnew.SHAPE_T_SEGMENT);g.SetLayer(pcbnew.F_SilkS);g.SetWidth(pcbnew.FromMM(lead['width_mm']));g.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(a[0]),pcbnew.FromMM(a[1])));g.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(c[0]),pcbnew.FromMM(c[1])));b.Add(g);keep.append(g)
print('references',len(data['labels']),'polarity strokes moved',changes)
pcbnew.SaveBoard(str(r/'640A_PowerAmp.kicad_pcb'),b)
json.dump({'c29_polarity_strokes_moved':changes,'delta_mm':[-2,0]},open(r/'polarity_marker_change.json','w'),indent=2)
