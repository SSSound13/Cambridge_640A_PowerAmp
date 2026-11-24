"""Dimensioned drawing: cylindrical button seat blending into one conical wall.

Drawing-only revision. A solid is constructed in memory to obtain the true
section; no STEP is exported. All dimensions in mm.
"""
from pathlib import Path
import argparse
import json
import math
import numpy as np
import cadquery as cq
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.patches import Rectangle, Polygon

ROOT=Path(__file__).resolve().parent
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output-dir',type=Path,default=ROOT/'drawing_output')
OUT=parser.parse_args().output_dir
OUT.mkdir(parents=True,exist_ok=True)

H=5.0
FOOT_H=.5
RI=4.15
FOOT_RO=5.9
SEAT_H=1.5
SEAT_W=.8
SEAT_RO=RI+SEAT_W
TOP_RO=7.25
WALL_W=.7
BLEND_RO=.5
BLEND_RI=BLEND_RO+SEAT_W
BASE_FILLET=.15
SHAFT_R=4.1
HEAD_R=6.0

# A circular arc joins the vertical cylinder to a straight cone tangentially.
# TOP_RO is fixed; solve the angle so that the cone reaches it exactly at H.
lo,hi=0.0,math.radians(70)
for _ in range(90):
    theta=(lo+hi)/2
    delta=BLEND_RO+(H-SEAT_H)*math.tan(theta)-BLEND_RO/math.cos(theta)
    if delta<TOP_RO-SEAT_RO:
        lo=theta
    else:
        hi=theta
theta=(lo+hi)/2
S,C=math.sin(theta),math.cos(theta)
center_r=SEAT_RO+BLEND_RO
def outer_arc(a):
    return (center_r-BLEND_RO*math.cos(a),SEAT_H+BLEND_RO*math.sin(a))
def inner_arc(a):
    return (center_r-BLEND_RI*math.cos(a),SEAT_H+BLEND_RI*math.sin(a))
arc_end=outer_arc(theta)
inner_arc_end=inner_arc(theta)
TAPER_SPAN=1.2

def smoothstep(t):
    t=max(0.0,min(1.0,t))
    return t*t*(3-2*t)
def width(z):
    return SEAT_W-(SEAT_W-WALL_W)*smoothstep((z-arc_end[1])/TAPER_SPAN)
def cone_inner(z):
    r=arc_end[0]+math.tan(theta)*(z-arc_end[1])
    w=width(z)
    return (r-C*w,z+S*w)

lo,hi=arc_end[1],H
for _ in range(75):
    z=(lo+hi)/2
    if cone_inner(z)[1]<H:lo=z
    else:hi=z
curve=np.array([cone_inner(z) for z in np.linspace(arc_end[1],(lo+hi)/2,161)])
curve[0]=inner_arc_end
curve[-1,1]=H
assert np.all(np.diff(curve[:,1])>0)
assert abs(cone_inner(arc_end[1])[0]-inner_arc_end[0])<1e-10

profile=(cq.Workplane('XZ').moveTo(RI,0).lineTo(FOOT_RO,0)
         .lineTo(FOOT_RO,FOOT_H).lineTo(SEAT_RO,FOOT_H)
         .lineTo(SEAT_RO,SEAT_H)
         .threePointArc(outer_arc(theta/2),arc_end)
         .lineTo(TOP_RO,H).lineTo(*curve[-1]))
profile=profile.spline([tuple(p) for p in curve[-2::-1]],includeCurrent=True)
profile=(profile.threePointArc(inner_arc(theta/2),(RI,SEAT_H))
         .lineTo(RI,0).close())
solid=profile.revolve(360,(0,0),(0,1)).val()
edges=[e for e in solid.Edges() if e.geomType()=='CIRCLE'
       and abs(e.Center().z-FOOT_H)<1e-6 and abs(e.radius()-SEAT_RO)<1e-6]
assert len(edges)==1
solid=solid.fillet(BASE_FILLET,edges)
assert solid.isValid() and len(solid.Solids())==1
bb=solid.BoundingBox()
assert abs(bb.zlen-H)<1e-5 and abs(bb.xlen-2*TOP_RO)<1e-5
# Verify a straight cylindrical bore, with no intrusion into the button passage.
passage=cq.Solid.makeCylinder(RI-1e-5,H+.2,cq.Vector(0,0,-.1))
assert solid.intersect(passage).Volume()<1e-7
seat_faces=[f for f in solid.Faces() if f.geomType()=='CYLINDER'
            and abs(f.BoundingBox().xlen-2*RI)<1e-5]
assert len(seat_faces)==1 and abs(seat_faces[0].BoundingBox().zlen-SEAT_H)<1e-5
# The figure uses the actual axial section of this single, continuous shell.
slab=cq.Workplane('XY').box(20,.002,7).translate((0,0,2.5)).val()
section=solid.intersect(slab)
assert section.isValid() and len(section.Solids())==2

INK='#20313A'; BLUE='#329BC4'; BLUE_DARK='#146889'
GREY='#D8DDE0'; MUTED='#52646F'; ORANGE='#AD5816'; DIM='#3C4F5A'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':12,'svg.fonttype':'none'})
fig=plt.figure(figsize=(14.4,9.0),dpi=200,facecolor='white')
ax=fig.add_axes([.035,.18,.93,.69])
ax.set_aspect('equal'); ax.set_xlim(-10.3,10.3); ax.set_ylim(-1.65,7.15); ax.axis('off')

ax.add_patch(Polygon([(-HEAD_R,-.65),(HEAD_R,-.65),(HEAD_R,0),
                      (SHAFT_R,0),(SHAFT_R,6),(-SHAFT_R,6),
                      (-SHAFT_R,0),(-HEAD_R,0)],closed=True,
                     facecolor=GREY,edgecolor=MUTED,lw=1.2,zorder=1))
for x in [-9.2,4.4]:
    ax.add_patch(Rectangle((x,H),4.8,.5,facecolor='#ECEFF1',edgecolor=MUTED,
                          hatch='///',lw=1.0,zorder=1))
ax.plot([0,0],[-.9,6.15],color='#92A0A8',lw=.9,ls=(0,(8,4,2,4)),zorder=2)

for part in section.Solids():
    vertices,triangles=part.tessellate(.004,.025)
    vertices=np.array([v.toTuple() for v in vertices]); triangles=np.asarray(triangles,dtype=int)
    ax.add_collection(PolyCollection(vertices[triangles][:,:,[0,2]],facecolors=BLUE,
                                    edgecolors='none',antialiaseds=False,zorder=4))
    for edge in part.Edges():
        pts,_=edge.sample(100)
        a=np.array([p.toTuple() for p in pts])
        ax.plot(a[:,0],a[:,2],color=BLUE_DARK,lw=.9,zorder=5)
for x in [-RI,SHAFT_R]:
    ax.add_patch(Rectangle((x,0),RI-SHAFT_R,SEAT_H,
                          facecolor='#EAB785',edgecolor='none',zorder=6))

def hdim(x1,x2,y,text,origin=None,color=DIM,below=False):
    if origin is not None:
        for x in [x1,x2]: ax.plot([x,x],[origin,y],color=color,lw=.65,zorder=7)
    ax.annotate('',xy=(x1,y),xytext=(x2,y),
                arrowprops=dict(arrowstyle='<->',color=color,lw=.95,shrinkA=0,shrinkB=0),zorder=8)
    ax.text((x1+x2)/2,y+(-.15 if below else .17),text,ha='center',
            va='top' if below else 'bottom',color=color,fontsize=12.5,
            bbox=dict(facecolor='white',edgecolor='none',pad=1.5),zorder=9)

hdim(-TOP_RO,TOP_RO,6.6,'Ø14,5 — широкий край у панели',origin=5.02)
hdim(-SHAFT_R,SHAFT_R,3.2,'Центральная часть кнопки Ø8,2')
hdim(-RI,RI,.72,'Внутренний Ø8,3',color=ORANGE)
hdim(-HEAD_R,HEAD_R,-1.15,'Шляпка кнопки Ø12',origin=-.69,below=True)

for z,x1 in [(0,FOOT_RO),(H,TOP_RO)]:
    ax.plot([x1,8.5],[z,z],color=DIM,lw=.65,zorder=7)
ax.annotate('',xy=(8.3,H),xytext=(8.3,0),
            arrowprops=dict(arrowstyle='<->',lw=1.05,color=DIM,shrinkA=0,shrinkB=0),zorder=8)
ax.text(8.56,2.5,'5,0 мм — свободная высота',rotation=90,ha='left',va='center',
        fontsize=12.5,color=INK,zorder=9)
# This height is measured from the underside of the foot, not added on top of it.
for z,x1 in [(0,FOOT_RO),(SEAT_H,SEAT_RO)]:
    ax.plot([x1,6.65],[z,z],color=ORANGE,lw=.65,zorder=7)
ax.annotate('',xy=(6.4,SEAT_H),xytext=(6.4,0),
            arrowprops=dict(arrowstyle='<->',lw=.95,color=ORANGE,shrinkA=0,shrinkB=0),zorder=8)
ax.text(6.66,.75,'1,5 мм',rotation=90,ha='left',va='center',fontsize=12,color=ORANGE,zorder=9)

def leader(text,xy,xytext,color=INK,angle=True):
    ax.annotate(text,xy=xy,xytext=xytext,ha='left',va='center',fontsize=12,
                color=color,bbox=dict(facecolor='white',edgecolor='none',pad=2),
                arrowprops=dict(arrowstyle='-',lw=.9,color=color,
                    connectionstyle='angle,angleA=0,angleB=90,rad=0' if angle else 'arc3,rad=0'),zorder=10)

leader('Плоская панель',(-7.8,5.28),(-9.5,5.95))
leader('Конус\nстенка 0,70 мм',(-6.0,3.8),(-9.5,4.1),color=BLUE_DARK,angle=False)
leader('Цилиндрическая\nпосадка\nстенка 0,80 мм',(-4.65,1.16),(-9.5,2.1),color=BLUE_DARK,angle=False)
leader('Пятка Ø11,8\nтолщина 0,5 мм',(-5.55,.24),(-9.5,-.1),color=BLUE_DARK,angle=False)

fig.text(.045,.945,'Демпфер с цилиндрической посадкой на кнопку',fontsize=22,weight='bold',color=INK)
fig.text(.045,.900,'Один непрерывный профиль: цилиндрический участок плавно переходит в конус',fontsize=12.5,color=MUTED)
fig.text(.045,.139,'Посадочный цилиндр: Ø8,3 внутри, Ø9,9 снаружи; длина 1,5 мм включает пятку.',
         fontsize=13,color=ORANGE,weight='bold')
fig.text(.045,.102,'Переход в конус: снаружи R0,5, внутри R1,3. Выше перехода стенка плавно утончается до 0,70 мм.',
         fontsize=11.5,color=MUTED)
fig.text(.045,.066,'Ø8,3 оставлен для этого эскиза; окончательный размер посадки зависит от фактических размеров кнопки и печати.',
         fontsize=11.0,color=INK)
fig.text(.045,.031,'Синий — цельный демпфер. Серый — кнопка. Демпфер без сжатия; толщина панели и шляпки показана условно.',
         fontsize=10.5,color=MUTED)

for ext in ['png','svg']:
    fig.savefig(OUT/f'damper_01_H5_section.{ext}',dpi=200,facecolor='white')
meta={'revision':'H5 cylindrical seating section; drawing only',
      'units':'mm','free_height':H,'foot_inner_diameter':2*RI,
      'foot_outer_diameter':2*FOOT_RO,'foot_height':FOOT_H,
      'seat_inner_diameter':2*RI,'seat_outer_diameter':2*SEAT_RO,
      'seat_length_including_foot':SEAT_H,'seat_wall_thickness':SEAT_W,
      'cone_upper_outer_diameter':2*TOP_RO,'cone_main_wall_normal_thickness':WALL_W,
      'blend_outer_radius':BLEND_RO,'blend_inner_radius':BLEND_RI,
      'foot_to_cylinder_outer_fillet':BASE_FILLET,
      'cone_angle_from_axis_deg':math.degrees(theta),
      'cone_wall_thinning_axial_interval':[arc_end[1],arc_end[1]+TAPER_SPAN],
      'button_central_diameter_previous_measurement':2*SHAFT_R,
      'button_head_diameter_previous_measurement':2*HEAD_R,
      'printed_bore_diameter':None,'step_exported':False,
      'solid_valid':solid.isValid(),'solid_count':len(solid.Solids()),
      'height_checked':bb.zlen,'outer_diameter_checked':bb.xlen,
      'minimum_passage_checked':2*RI,'cylindrical_seat_length_checked':seat_faces[0].BoundingBox().zlen}
(OUT/'dimensions.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(meta,ensure_ascii=False,indent=2))
print(OUT/'damper_01_H5_section.png')
