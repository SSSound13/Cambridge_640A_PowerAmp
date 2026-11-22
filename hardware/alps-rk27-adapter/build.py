"""Run with KiCad 10 Python. Coordinates: X right viewed from shaft; D rearward.
ALPS dimensions from K272AMC02C and motor-driven catalogue drawing 6.
"""
from pathlib import Path
import uuid, json, shutil, os
import pcbnew as p
import math

ROOT=Path(__file__).resolve().parent
LIB=ROOT/'Adapter.pretty'
LIB.mkdir(exist_ok=True)
def savefp(f): p.PCB_IO_MGR.FindPlugin(p.PCB_IO_MGR.KICAD_SEXP).FootprintSave(str(LIB),f)
KICAD=Path(p.__file__).resolve().parents[1]
FP=KICAD/'share/kicad/footprints'
if not FP.exists(): FP=Path(os.environ.get('LOCALAPPDATA',''))/'Programs/KiCad/10.0/share/kicad/footprints'
def uid(s): return str(uuid.uuid5(uuid.NAMESPACE_URL,'cambridge/alps-adapter/'+s))
def mm(x,y): return p.VECTOR2I(p.FromMM(x),p.FromMM(y))
def q(s): return json.dumps(str(s))
def eff(size=1.27): return f'(effects (font (size {size} {size})))'

MODELS=ROOT/'Adapter.3dshapes';MODELS.mkdir(exist_ok=True)
def mesh(vertices,faces,color):
 pts=', '.join(' '.join(f'{v/2.54:.6f}' for v in pt) for pt in vertices)
 idx=', '.join(' '.join(map(str,f))+ ' -1' for f in faces)
 return f'Shape {{ appearance Appearance {{ material Material {{ diffuseColor {color} specularColor 0.25 0.25 0.25 shininess 0.35 }} }} geometry IndexedFaceSet {{ solid TRUE coord Coordinate {{ point [ {pts} ] }} coordIndex [ {idx} ] }} }}\n'
def box(x1,x2,y1,y2,z1,z2,col):
 return mesh([(x1,y1,z1),(x2,y1,z1),(x2,y2,z1),(x1,y2,z1),(x1,y1,z2),(x2,y1,z2),(x2,y2,z2),(x1,y2,z2)],[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],col)
def cyl(x,z,y1,y2,r,col):
 n=64;verts=[(x+r*math.cos(i*math.tau/n),y,z+r*math.sin(i*math.tau/n)) for y in (y1,y2) for i in range(n)]
 faces=[tuple(range(n)),tuple(range(2*n-1,n-1,-1))]+[(i,i+n,(i+1)%n+n,(i+1)%n) for i in range(n)]
 return mesh(verts,faces,col)
silver='.68 .70 .73';blue='.035 .15 .35';dark='.06 .065 .075';brass='.65 .52 .23'
v='#VRML V2.0 utf8\n# Simplified ALPS K272AMC02C envelope. Units 0.1 inch. Not vendor CAD.\n'
v+=box(-13.5,13.5,2,3.2,0,24.5,silver)
v+=box(-12.5,12.5,3.2,31.6,.5,24.5,blue)
for y in (11,21,31):v+=box(-13,13,y,y+.6,.4,25,dark)
v+=box(-13.5,22.7,31.6,46.7,.5,28.5,silver)
v+=cyl(10.5,12.5,46.7,64.8,12.2,silver)
v+=cyl(10.5,12.5,64.8,66.7,11.8,dark)
v+=box(-1.75,22.65,66.7,68.35,.5,24.5,'.2 .28 .13')
v+=cyl(0,12.5,-7,0,4,brass)+cyl(0,12.5,-20,-6.9,3,silver)
v+=cyl(0,12.5,0,2,3,silver) # simplified neck between mounting plane and front plate
v+=cyl(-10,12.5,0,2,1.5,silver)
for d in (5,15):
 for x in (-5,0,5):v+=box(x-.5,x+.5,d-.2,d+.2,-4,1,brass)
for x in (-7,11.5):v+=box(x-1.3,x+1.3,45.2,45.8,-4,1,silver)
for x in (2,19):v+=box(x-.4,x+.4,65.95,66.45,-4,1,brass)
(MODELS/'ALPS_RK27112MC_envelope.wrl').write_text(v)
def model(f,filename):
 m=p.FP_3DMODEL();m.m_Filename='${KIPRJMOD}/Adapter.3dshapes/'+filename;f.Add3DModel(m)

# Supplier library is user-provided and deliberately not redistributed.
VENDOR=ROOT/'vendor-local/SamacSys.pretty'
if not (VENDOR/'RK27112MC.kicad_mod').exists():
 raise RuntimeError('Install RK27112MC.kicad_mod from the licensed supplier archive into vendor-local/SamacSys.pretty')
(ROOT/'fp-lib-table').write_text('(fp_lib_table (version 7) (lib (name "SamacSys") (type "KiCad") (uri "${KIPRJMOD}/vendor-local/SamacSys.pretty") (options "") (descr "User-installed supplier library")))\n')

NAMES=['R1_LOW','R1_WIPER','R1_HIGH','R2_LOW','R2_WIPER','R2_HIGH','MOTOR_A','MOTOR_B']
defs={}
def symbol(name,names,ref):
 height=(len(names)+1)*2.54
 s=f'(symbol {q(name)} (pin_names (offset 1.016)) (in_bom yes) (on_board yes) (property "Reference" {q(ref)} (at 0 5.08 0) {eff()}) (property "Value" {q(name)} (at 0 2.54 0) {eff()})'
 s+=f'(symbol {q(name+"_0_1")} (rectangle (start 0 0) (end 25.4 {-height}) (stroke (width 0.254) (type default)) (fill (type background))))'
 s+=f'(symbol {q(name+"_1_1")} '
 for i,n in enumerate(names):s+=f'(pin passive line (at -5.08 {-2.54*(i+1)} 0) (length 5.08) (name {q(n)} {eff(1.016)}) (number "{i+1}" {eff(1.016)}))'
 return s+'))'
defs['RK27112MC_PCBMotor']=symbol('RK27112MC_PCBMotor',NAMES[:6]+['MECHANICAL_7','MECHANICAL_8'],'RV')
defs['Audio6']=symbol('Audio6',NAMES[:6],'J')
defs['Motor2']=symbol('Motor2',NAMES[6:],'J')
defs['Mount']=symbol('Mount',[],'H')
defs['MotorPad']=symbol('MotorPad',['MOTOR_TERMINAL'],'MP')
(ROOT/'Adapter.kicad_sym').write_text('(kicad_symbol_lib (version 20241209) (generator "kicad_symbol_editor") '+''.join(defs.values())+')',encoding='utf-8')
(ROOT/'sym-lib-table').write_text('(sym_lib_table (version 7) (lib (name "Adapter") (type "KiCad") (uri "${KIPRJMOD}/Adapter.kicad_sym") (options "") (descr "Adapter symbols")))\n')
rootid=uid('root')
s=f'(kicad_sch (version 20250114) (generator "eeschema") (uuid {rootid}) (paper "A4") (title_block (title "ALPS RK27112MC adapter - fit confirmation required") (rev "A-draft")) (lib_symbols '
for name,value in defs.items(): s+=value.replace(f'(symbol "{name}"',f'(symbol "Adapter:{name}"',1)
s+=')'
items=[('RV1','RK27112MC_PCBMotor','SamacSys:RK27112MC',100,50,NAMES[:6]+['MECHANICAL_7','MECHANICAL_8'],'RK27112MC / value TBC'),('J1','Audio6','Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical',50,50,NAMES[:6],'1x06 / 2.54 mm'),('J2','Motor2','Connector_JST:JST_PH_B2B-PH-K_1x02_P2.00mm_Vertical',50,90,NAMES[6:],'B2B-PH-K-S')]
# Use explicit JST name (loop above changes name).
items[2]=('J2','Motor2','Connector_JST:JST_PH_B2B-PH-K_1x02_P2.00mm_Vertical',50,90,NAMES[6:],'B2B-PH-K-S')
for ref,x,n in [('MP1',100,NAMES[6]),('MP2',145,NAMES[7])]:items.append((ref,'MotorPad','TestPoint:TestPoint_THTPad_D2.5mm_Drill1.2mm',x,95,[n],'Motor PCB terminal'))
for i in range(4):items.append((f'H{i+1}','Mount','MountingHole:MountingHole_3.2mm_M3',50+i*40,125,[],'M3 / 3.2 mm'))
for ref,sym,fp,x,y,names,value in items:
 x=round(x/2.54)*2.54;y=round(y/2.54)*2.54
 s+=f'(symbol (lib_id "Adapter:{sym}") (at {x} {y} 0) (unit 1) (in_bom {"no" if ref.startswith(("H","MP")) else "yes"}) (on_board yes) (dnp no) (uuid {uid(ref)})'
 for prop,val,yy in [('Reference',ref,y-5.08),('Value',value,y-2.54),('Footprint',(fp if ':' in fp else 'Adapter:'+fp),y)]:
  s+=f'(property {q(prop)} {q(val)} (at {x+12.7} {yy} 0) (effects (font (size 1.27 1.27))'+(' (hide yes)' if prop=='Footprint' else '')+'))'
 for i in range(len(names)):s+=f'(pin "{i+1}" (uuid {uid(ref+str(i))}))'
 s+=f'(instances (project "alps-rk27-adapter" (path "/{rootid}" (reference "{ref}") (unit 1)))))'
 for i,n in enumerate(names):
  yy=y+2.54*(i+1)
  if n.startswith('MECHANICAL_'):
   s+=f'(no_connect (at {x-5.08} {yy}) (uuid {uid(ref+n+"nc")}))'
   continue
  s+=f'(wire (pts (xy {x-5.08} {yy}) (xy {x-15.24} {yy})) (stroke (width 0) (type default)) (uuid {uid(ref+n+"wire")}))'
  s+=f'(label {q(n)} (at {x-15.24} {yy} 0) (effects (font (size 1 1)) (justify left bottom)) (uuid {uid(ref+n+"label")}))'
for i,t in enumerate(['Pin order J1: R1 low, wiper, high; R2 low, wiper, high.', 'R1 is front section. 1=CCW, 2=wiper, 3=CW (ALPS drawing).','Motor polarity is NOT assigned: verify rotation on actual part.', 'Four M3 axes shared with expanded R4 lower PCB.', 'Mechanical fit and actual part code remain to be confirmed.']):
 s+=f'(text {q(t)} (at 45 {155+i*5} 0) (effects (font (size 1.27 1.27)) (justify left)) (uuid {uid(t)}))'
s+=')'
(ROOT/'alps-rk27-adapter.kicad_sch').write_text(s,encoding='utf-8')
print('Libraries and schematic generated')
(ROOT/'alps-rk27-adapter.kicad_pro').write_text(json.dumps({'meta':{'filename':'alps-rk27-adapter.kicad_pro','version':1},'board':{'design_settings':{'rules':{'min_clearance':0.25,'min_track_width':0.25,'min_hole_clearance':0.25,'min_copper_edge_clearance':0.5}}}},indent=2))

# Front edge matches supplied R3 reference: front row setback = 3.5 mm, from manual artwork.
b=p.BOARD();b.SetCopperLayerCount(2);b.GetDesignSettings().SetBoardThickness(p.FromMM(1.6))
def pos(x,d):return mm(85+x,140-d)
nets={}
for i,n in enumerate(NAMES):
 net=p.NETINFO_ITEM(b,'/'+n,i+1);b.Add(net);nets[n]=net
for number in (7,8):
 key='MECHANICAL_'+str(number)
 net=p.NETINFO_ITEM(b,f'unconnected-(RV1-{key}-Pad{number})',number+2);b.Add(net);nets[key]=net
fps={}
def place(ref,fp,x,d,value):
 lib,part=fp.split(':',1) if ':' in fp else ('Adapter',fp)
 f=p.FootprintLoad(str(VENDOR) if lib=='SamacSys' else str(FP/(lib+'.pretty')),part);f.SetFPID(p.LIB_ID(lib,part));f.SetReference(ref);f.SetValue(value)
 if ref=='J1':f.SetOrientationDegrees(180)
 if ref=='RV1':
  for graphic in f.GraphicalItems():
   if graphic.GetLayer()==p.F_SilkS:graphic.SetLayer(p.F_Fab) # supplier assembly outline crosses board edge
  f.Models().clear()
  m=p.FP_3DMODEL();m.m_Filename='${KIPRJMOD}/Adapter.3dshapes/ALPS_RK27112MC_envelope.wrl';m.m_Rotation.z=-90;m.m_Offset.x=45.5;f.Add3DModel(m)
  p.PCB_IO_MGR.FindPlugin(p.PCB_IO_MGR.KICAD_SEXP).FootprintSave(str(VENDOR),f)
  f.SetOrientationDegrees(-90)
 f.SetPosition(pos(x,d))
 path=p.KIID_PATH();path.push_back(p.KIID(rootid));path.push_back(p.KIID(uid(ref)));f.SetPath(path)
 f.Reference().SetVisible(False);f.Value().SetVisible(False);b.Add(f);fps[ref]=f
 return f
for ref,sym,fp,x,y,ns,value in items:
 xx,dd={'RV1':(0,45.5),'MP1':(2,66.2),'MP2':(19,66.2),'J1':(-20,15),'J2':(-19,62),'H1':(-21,43.5),'H2':(27,6.2),'H3':(-21,74),'H4':(27,74)}[ref]
 f=place(ref,fp,xx,dd,value)
 for a in f.Pads():
  if a.GetNumber() and ns[int(a.GetNumber())-1] in nets:a.SetNet(nets[ns[int(a.GetNumber())-1]])
for a,c in [((-25,1.5),(31,1.5)),((31,1.5),(31,78)),((31,78),(-25,78)),((-25,78),(-25,1.5))]:
 e=p.PCB_SHAPE();e.SetShape(p.SHAPE_T_SEGMENT);e.SetStart(pos(*a));e.SetEnd(pos(*c));e.SetWidth(p.FromMM(.05));e.SetLayer(p.Edge_Cuts);b.Add(e)
def textboard(s,x,d,size=1,layer=p.F_SilkS):
 t=p.PCB_TEXT(b);t.SetText(s);t.SetPosition(pos(x,d));t.SetTextSize(mm(size,size));t.SetTextThickness(p.FromMM(.15));t.SetLayer(layer);b.Add(t)
textboard('FRONT / SHAFT',4,3,1,p.F_Fab)
textboard('RK27 ADAPTER - DRAFT',3,71,1)
textboard('FRONT DATUM: MANUAL 3.5',3,76, .85)
textboard('J1',-17,12,1)
for i in range(6):textboard(str(i+1),-23,15+i*2.54,.8)
textboard('J2 MOTOR',-18,57, .9)
for i,(x,d) in enumerate([(-21,43.5),(27,6.2),(-21,74),(27,74)]):
 textboard('H'+str(i+1),x,d+(5 if d<20 else -5),.8)
 # Explicit copper/track/via keepout diameter 7 mm on BOTH copper layers.
 z=p.ZONE(b);z.SetIsRuleArea(True);z.SetLayerSet(p.LSET.AllCuMask());z.SetDoNotAllowTracks(True);z.SetDoNotAllowVias(True);z.SetDoNotAllowZoneFills(True);z.SetDoNotAllowPads(False);z.SetDoNotAllowFootprints(False)
 poly=z.Outline();poly.NewOutline()
 import math
 for k in range(64):
  v=pos(x+3.5*math.cos(k*math.tau/64),d+3.5*math.sin(k*math.tau/64));poly.Append(v.x,v.y)
 b.Add(z)

# Small two-layer grid router. DRC is the authoritative clearance check.
import heapq, math
STEP=.25;NX=225;NY=313
def grid(x,d):return (round((x+25)/STEP),round(d/STEP))
def coord(g):return(g[0]*STEP-25,g[1]*STEP)
padinfo=[]
for f in b.GetFootprints():
 for a in f.Pads():
  x=p.ToMM(a.GetPosition().x)-85;d=140-p.ToMM(a.GetPosition().y)
  r=max(p.ToMM(a.GetSize().x),p.ToMM(a.GetSize().y))/2
  if f.GetReference().startswith('H'):r=3.5
  padinfo.append((x,d,r,a.GetNetname().lstrip('/')))
occupied=[set(),set()]
def disk(target,x,d,r):
 gx,gy=grid(x,d);n=math.ceil(r/STEP)+1
 for ix in range(max(0,gx-n),min(NX,gx+n+1)):
  for iy in range(max(0,gy-n),min(NY,gy+n+1)):
   xx,dd=coord((ix,iy))
   if (xx-x)**2+(dd-d)**2<r*r:target.add((ix,iy))
def addseg(a,c,layer,net):
 if a==c:return
 tr=p.PCB_TRACK(b);tr.SetStart(pos(*a));tr.SetEnd(pos(*c));tr.SetWidth(p.FromMM(.3));tr.SetLayer([p.F_Cu,p.B_Cu][layer]);tr.SetNet(nets[net]);b.Add(tr)
 length=math.dist(a,c)
 for k in range(max(1,math.ceil(length/.1))+1):
  f=k/max(1,math.ceil(length/.1));disk(occupied[layer],a[0]+f*(c[0]-a[0]),a[1]+f*(c[1]-a[1]),.56)
def route(net,start,end):
 blocked=[set(occupied[0]),set(occupied[1])]
 for x,d,r,n in padinfo:
  if n!=net:
   for layer in (0,1):disk(blocked[layer],x,d,r+.41)
 a=grid(*start);c=grid(*end)
 starts=[(*a,0),(*a,1)];dist={s:0 for s in starts};prev={};heap=[]
 def heuristic(x,y):return (abs(x-c[0])+abs(y-c[1]))*.71
 for ss in starts:heapq.heappush(heap,(heuristic(*a),0,ss))
 finish=None
 while heap:
  _,cost,u=heapq.heappop(heap)
  if cost!=dist.get(u):continue
  x,y,l=u
  if (x,y)==c:finish=u;break
  moves=[(x+dx,y+dy,l,1.414214 if dx and dy else 1) for dx,dy in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(-1,1),(1,-1),(-1,-1)]]
  if all((x+dx,y+dy) not in blocked[ll] for ll in (0,1) for dx in (-1,0,1) for dy in (-1,0,1)):
   moves.append((x,y,1-l,30))
  for xx,yy,ll,w in moves:
   if not(3<=xx<NX-3 and 12<=yy<NY-3) or (xx,yy) in blocked[ll]:continue
   if xx!=x and yy!=y and ((xx,y) in blocked[ll] or (x,yy) in blocked[ll]):continue
   v=(xx,yy,ll);nc=cost+w
   if nc<dist.get(v,1e99):dist[v]=nc;prev[v]=u;heapq.heappush(heap,(nc+heuristic(xx,yy),nc,v))
 if finish is None:raise RuntimeError('No route for '+net)
 path=[finish]
 while path[-1] in prev:path.append(prev[path[-1]])
 path.reverse()
 addseg(start,coord(path[0]),path[0][2],net)
 # Coalesce straight runs to keep editable native tracks.
 anchor=path[0];last=path[0];direction=None
 for v in path[1:]:
  newdir=(v[0]-last[0],v[1]-last[1],v[2]-last[2])
  if v[2]!=last[2]:
   addseg(coord(anchor),coord(last),last[2],net)
   via=p.PCB_VIA(b);via.SetPosition(pos(*coord(v)));via.SetWidth(p.FromMM(.7));via.SetDrill(p.FromMM(.3));via.SetViaType(p.VIATYPE_THROUGH);via.SetLayerPair(p.F_Cu,p.B_Cu);via.SetNet(nets[net]);b.Add(via)
   for layer in (0,1):disk(occupied[layer],*coord(v),.76)
   anchor=v;direction=None
  elif direction is not None and newdir!=direction:
   addseg(coord(anchor),coord(last),last[2],net);anchor=last
  direction=newdir;last=v
 addseg(coord(anchor),coord(last),last[2],net);addseg(coord(last),end,last[2],net)
 print('Routed',net)
for i,n in enumerate(NAMES[:6]):route(n,(-20,15+2.54*i),([-5,0,5][i%3],[5,15][i//3]))
# JST factory footprint has pin 2 +2 mm in X, same depth as pin 1.
route('MOTOR_A',(-19,62),(2,66.2));route('MOTOR_B',(-17,62),(19,66.2))
p.SaveBoard(str(ROOT/'alps-rk27-adapter.kicad_pcb'),b)
print('Draft PCB generated; front datum corrected to manual-derived 3.5 mm')
