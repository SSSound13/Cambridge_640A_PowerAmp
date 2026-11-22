from pathlib import Path
import re,json,math,collections,subprocess
r=Path('.')
# Check exported VRML geometry, not just generator parameters.
s=(r/'Adapter.3dshapes/ALPS_RK27112MC_envelope.wrl').read_text()
checks=[]
for points,indices in re.findall(r'point \[ (.*?) \].*?coordIndex \[ (.*?) \]',s):
 v=[tuple(float(a)*2.54 for a in row.split()) for row in points.split(',')]
 faces=[list(map(int,f.split())) for f in indices.replace(',',' ').split('-1') if f.strip()]
 edges=collections.Counter();vol=0
 for face in faces:
  for a,b in zip(face,face[1:]+face[:1]):edges[tuple(sorted((a,b)))]+=1
  a=v[face[0]]
  for i in range(1,len(face)-1):
   b,c=v[face[i]],v[face[i+1]]
   vol+=(a[0]*(b[1]*c[2]-b[2]*c[1])+a[1]*(b[2]*c[0]-b[0]*c[2])+a[2]*(b[0]*c[1]-b[1]*c[0]))/6
 assert vol>0 and set(edges.values())=={2}
 checks.append({'volume_mm3':round(vol,3),'closed_edges':True,'outward_winding':True})
(r/'validation/model_geometry.json').write_text(json.dumps({'meshes':checks,'shaft_axis':[0,1,0],'motor_axis':[0,1,0],'axis_height_mm':12.5,'motor_lateral_offset_mm':10.5,'limitations':'Simplified envelope, not vendor CAD; dimensions not a substitute for actual part fit.'},indent=2))
cli='C:/Users/Stas/AppData/Local/Programs/KiCad/10.0/bin/kicad-cli.exe'
commands=[['pcb','drc','--schematic-parity','--format','json','-o','validation/drc.json','alps-rk27-adapter.kicad_pcb'],['sch','erc','--format','json','-o','validation/erc.json','alps-rk27-adapter.kicad_sch'],['sch','export','pdf','-o','renders/schematic.pdf','alps-rk27-adapter.kicad_sch'],['sch','export','svg','-o','renders/','alps-rk27-adapter.kicad_sch'],['pcb','export','svg','--layers','F.Cu,B.Cu,F.SilkS,F.Fab,Edge.Cuts','--mode-single','--fit-page-to-board','--exclude-drawing-sheet','-o','renders/layout.svg','alps-rk27-adapter.kicad_pcb']]
for side in ['assembly','top','bottom','right','front']:
 commands.append(['pcb','render','--width','1400','--height','1200','--background','opaque','--zoom','0.65']+(['--rotate','325,0,25'] if side=='assembly' else ['--side',side])+['-o','renders/'+side+'.png','alps-rk27-adapter.kicad_pcb'])
for args in commands:
 p=subprocess.run([cli]+args,capture_output=True,text=True);print(' '.join(args[:3]),p.returncode,flush=True)
 if p.returncode:print(p.stdout,p.stderr);raise SystemExit(p.returncode)
