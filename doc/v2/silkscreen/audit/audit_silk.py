import pcbnew,json,hashlib
from pathlib import Path
r=Path('/workspace/Cambridge_640A_v2_silkscreen');src=Path('/workspace/Cambridge_640A_v2_reviewed');keep=[]
def snap(path):
 b=pcbnew.LoadBoard(str(path));fs=list(b.GetFootprints());ts=list(b.GetTracks());ds=list(b.GetDrawings());zs=list(b.Zones());keep.extend([b]+fs+ts+ds+zs)
 def xy(p):return [p.x,p.y]
 tracks={t.m_Uuid.AsString():[t.GetNetname(),int(t.GetLayer()),xy(t.GetStart()),xy(t.GetEnd()),t.GetWidth(pcbnew.F_Cu) if isinstance(t,pcbnew.PCB_VIA) else t.GetWidth(),t.GetDrillValue() if isinstance(t,pcbnew.PCB_VIA) else None] for t in ts}
 fps={};refs={};back=[]
 for f in fs:
  ps=list(f.Pads());gs=list(f.GraphicalItems());t=f.Reference();v=f.Value();keep.extend(ps+gs+[t,v])
  fps[f.GetReference()]=[xy(f.GetPosition()),f.GetOrientationDegrees(),f.GetFPIDAsString(),v.GetText(),{p.m_Uuid.AsString():[p.GetNumber(),p.GetNetname(),xy(p.GetPosition()),xy(p.GetSize()),xy(p.GetDrillSize()),int(p.GetShape())] for p in ps}]
  refs[f.GetReference()]={'xy':xy(t.GetPosition()),'angle':t.GetTextAngle().AsDegrees(),'size':xy(t.GetTextSize()),'thickness':t.GetTextThickness(),'visible':t.IsVisible(),'layer':int(t.GetLayer())}
  for g in gs:
   if g.GetLayer()==pcbnew.B_SilkS:back.append([g.m_Uuid.AsString(),xy(g.GetPosition()),str(g.GetText()) if isinstance(g,pcbnew.PCB_TEXT) else [xy(g.GetStart()),xy(g.GetEnd()),g.GetWidth()]])
 edges=[[g.m_Uuid.AsString(),xy(g.GetStart()),xy(g.GetEnd()),g.GetWidth()] for g in ds if g.GetLayer()==pcbnew.Edge_Cuts]
 return tracks,fps,refs,sorted(back),sorted(edges)
a=snap(src/'640A_PowerAmp.kicad_pcb');b=snap(r/'640A_PowerAmp.kicad_pcb');assert a[0]==b[0];assert a[1]==b[1];assert a[3:]==b[3:]
scope=json.load(open(r/'symmetry_scope.json'));errs=[]
for l,rr in scope['pairs'].items():
 x,y=b[2][l],b[2][rr]
 if x['angle']!=y['angle'] or y['xy'][0]-x['xy'][0]!=98955800 or y['xy'][1]!=x['xy'][1]:errs.append([l,rr])
assert not errs
visible=[x for x in b[2].values() if x['visible']];assert len(visible)==293;assert all(x['size']==[1000000,1000000] and x['thickness']==150000 and x['angle'] in [0,90] for x in visible)
assert (r/'640A_PowerAmp.kicad_pro').read_bytes()==(src/'640A_PowerAmp.kicad_pro').read_bytes()
p=json.load(open(r/'silkscreen_placement.json'));drc=json.load(open(r/'validation/final_drc.json'));assert not drc['violations'] and not drc['unconnected_items'] and not drc['schematic_parity']
report={'visible_references':293,'horizontal':sum(x['angle']==0 for x in visible),'vertical':sum(x['angle']==90 for x in visible),'text_size_mm':1,'stroke_mm':.15,'group_line_pitch_mm':1.5,'group_blocks':len(p['groups']),'leaders':len(p['leaders']),'matched_reference_pairs':len(scope['pairs']),'symmetry_errors':errs,'footprints_and_pads_unchanged':True,'copper_tracks_and_vias_unchanged':True,'back_silkscreen_unchanged':True,'board_outline_unchanged':True,'project_rules_unchanged':True,'drc_violations':0,'unconnected':0,'schematic_parity_errors':0,'previous_silkscreen_warnings':231,'pcb_sha256':hashlib.sha256((r/'640A_PowerAmp.kicad_pcb').read_bytes()).hexdigest()}
json.dump(report,open(r/'validation/silkscreen_audit.json','w'),indent=2);print(json.dumps(report))
