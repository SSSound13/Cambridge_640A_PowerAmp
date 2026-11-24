"""One dimensioned section of prototype 01 at H=5 mm; no STEP export.

The printed H4 design is kept as evidence.  Only free height is revised here.
The 8.3-mm CAD bore is shown, not claimed to be the measured printed bore.
"""
from pathlib import Path
import json
import math
import argparse
import numpy as np
import cadquery as cq
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.patches import Rectangle, Polygon

ROOT = Path(__file__).resolve().parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output-dir', type=Path, default=ROOT/'drawing_output')
OUT = parser.parse_args().output_dir
OUT.mkdir(parents=True, exist_ok=True)

H = 5.0
FOOT_H = 0.5
RI, RO, RTOP = 4.15, 5.9, 7.25
SHAFT_R, HEAD_R = 4.1, 6.0
DZ = H - FOOT_H
DR = RTOP - RO
S = DR / math.hypot(DR, DZ)
C = DZ / math.hypot(DR, DZ)
M = DR / DZ
ROOT_TRANSITION = 1.2 * DZ / 3.5

def smoothstep(t):
    t = max(0.0, min(1.0, t))
    return t*t*(3.0-2.0*t)

def thickness(z):
    return .85 - .15*smoothstep((z-FOOT_H)/ROOT_TRANSITION)

def inner_point(z):
    w = thickness(z)
    return (RO+M*(z-FOOT_H)-C*w, z+S*w)

def at_height(target):
    lo, hi = -1.0, H+1.0
    for _ in range(75):
        mid = (lo+hi)/2.0
        if inner_point(mid)[1] < target:
            lo = mid
        else:
            hi = mid
    return (lo+hi)/2.0

curve = np.array([inner_point(z) for z in np.linspace(at_height(FOOT_H), at_height(H), 161)])
curve[0, 1], curve[-1, 1] = FOOT_H, H
wp = (cq.Workplane('XZ').moveTo(RI, 0).lineTo(RO, 0)
      .lineTo(RO, FOOT_H).lineTo(RTOP, H).lineTo(*curve[-1]))
wp = wp.spline([tuple(p) for p in curve[-2::-1]], includeCurrent=True)
solid = wp.lineTo(RI, FOOT_H).close().revolve(360, (0, 0), (0, 1)).val()
edge = [e for e in solid.Edges() if e.geomType() == 'CIRCLE'
        and abs(e.Center().z-FOOT_H) < 1e-6 and abs(e.radius()-curve[0,0]) < 1e-6]
assert len(edge) == 1
solid = solid.fillet(.15, edge)
assert solid.isValid() and len(solid.Solids()) == 1
bb = solid.BoundingBox()
assert abs(bb.zlen-H) < 1e-5 and abs(bb.xlen-14.5) < 1e-5

# Render an actual axial section of the in-memory solid. No CAD file is exported.
slab = cq.Workplane('XY').box(20, .002, 7).translate((0, 0, 2.5)).val()
piece = solid.intersect(slab)
assert piece.isValid() and len(piece.Solids()) == 2

INK = '#20313A'
BLUE = '#329BC4'
BLUE_DARK = '#146889'
GREY = '#D8DDE0'
MUTED = '#52646F'
ORANGE = '#AD5816'
DIM = '#3C4F5A'
plt.rcParams.update({'font.family':'DejaVu Sans', 'font.size':12, 'svg.fonttype':'none'})
fig = plt.figure(figsize=(14.4, 9.0), dpi=200, facecolor='white')
ax = fig.add_axes([.035, .18, .93, .69])
ax.set_aspect('equal')
ax.set_xlim(-10.3, 10.3)
ax.set_ylim(-1.65, 7.15)
ax.axis('off')

# Rigid button and a flat plate. Their unmeasured thicknesses are illustrative.
ax.add_patch(Polygon([(-HEAD_R,-.65),(HEAD_R,-.65),(HEAD_R,0),
                      (SHAFT_R,0),(SHAFT_R,6),(-SHAFT_R,6),
                      (-SHAFT_R,0),(-HEAD_R,0)],closed=True,
                     facecolor=GREY,edgecolor=MUTED,lw=1.2,zorder=1))
for x in [-9.2, 4.4]:
    ax.add_patch(Rectangle((x,5),4.8,.5,facecolor='#ECEFF1',edgecolor=MUTED,
                           hatch='///',lw=1.0,zorder=1))
ax.plot([0,0],[-.9,6.15], color='#92A0A8', lw=.9, ls=(0,(8,4,2,4)), zorder=2)

for part in piece.Solids():
    vertices, triangles = part.tessellate(.004,.025)
    vertices = np.array([v.toTuple() for v in vertices])
    triangles = np.asarray(triangles,dtype=int)
    ax.add_collection(PolyCollection(vertices[triangles][:,:,[0,2]],
                       facecolors=BLUE,edgecolors='none',antialiaseds=False,zorder=4))
    for e in part.Edges():
        pts,_ = e.sample(100)
        a = np.array([p.toTuple() for p in pts])
        ax.plot(a[:,0],a[:,2],color=BLUE_DARK,lw=.9,zorder=5)

# The nominal diametral clearance is only 0.1 mm. Highlight its true scale.
for x in [-RI, SHAFT_R]:
    ax.add_patch(Rectangle((x,0),RI-SHAFT_R,FOOT_H,
                           facecolor='#EAB785',edgecolor='none',zorder=6))

def horizontal_dimension(x1, x2, y, text, origin=None, color=DIM, below=False):
    if origin is not None:
        for x in [x1,x2]:
            ax.plot([x,x],[origin,y],color=color,lw=.65,zorder=7)
    ax.annotate('',xy=(x1,y),xytext=(x2,y),
                arrowprops=dict(arrowstyle='<->',color=color,lw=.95,shrinkA=0,shrinkB=0),zorder=8)
    ax.text((x1+x2)/2,y+(-.15 if below else .17),text,ha='center',
            va='top' if below else 'bottom',color=color,fontsize=12.5,
            bbox=dict(facecolor='white',edgecolor='none',pad=1.5),zorder=9)

horizontal_dimension(-RTOP,RTOP,6.6,'Ø14,5 — широкий край у панели',origin=5.02)
horizontal_dimension(-SHAFT_R,SHAFT_R,3.0,'Центральная часть кнопки Ø8,2')
horizontal_dimension(-RI,RI,.24,'Посадочное отверстие Ø8,3',color=ORANGE)
horizontal_dimension(-HEAD_R,HEAD_R,-1.15,'Шляпка кнопки Ø12',origin=-.69,below=True)

for z,x1 in [(0,RO),(H,RTOP)]:
    ax.plot([x1,8.5],[z,z],color=DIM,lw=.65,zorder=7)
ax.annotate('',xy=(8.3,H),xytext=(8.3,0),
            arrowprops=dict(arrowstyle='<->',lw=1.05,color=DIM,shrinkA=0,shrinkB=0),zorder=8)
ax.text(8.56,2.5,'5,0 мм — свободная высота',rotation=90,ha='left',va='center',
        fontsize=12.5,color=INK,zorder=9)

def leader(text, xy, xytext, align='left', color=INK):
    ax.annotate(text,xy=xy,xytext=xytext,ha=align,va='center',fontsize=12.0,
                color=color,bbox=dict(facecolor='white',edgecolor='none',pad=2),
                arrowprops=dict(arrowstyle='-',lw=.9,color=color,
                                connectionstyle='angle,angleA=0,angleB=90,rad=0'),zorder=10)

leader('Плоская панель',(-7.8,5.28),(-9.5,5.95))
leader('Стенка\n0,70 мм',(-6.28,3.0),(-9.5,3.8),color=BLUE_DARK)
leader('Пятка\nØ11,8 снаружи\nтолщина 0,5 мм',(-5.3,.21),(-9.5,.9),color=BLUE_DARK)

fig.text(.045,.945,'Один образец: базовый демпфер, высота 5 мм',
         fontsize=22,weight='bold',color=INK)
fig.text(.045,.900,'Разрез через ось  ·  Синий — демпфер  ·  Серый — жёсткая кнопка',
         fontsize=12.5,color=MUTED)
fig.text(.045,.139,'Посадка в модели: Ø8,3 − Ø8,2 = 0,10 мм по диаметру; по 0,05 мм на сторону.',
         fontsize=13,color=ORANGE,weight='bold')
fig.text(.045,.102,'У корня стенка 0,85 мм, переход к пятке R0,15. Толщины стенки заданы поперёк её наклона.',
         fontsize=11.5,color=MUTED)
fig.text(.045,.066,'Ø8,3 — размер в модели. Фактическое отверстие напечатанного кольца ещё нужно измерить.',
         fontsize=11.5,color=INK)
fig.text(.045,.031,'Демпфер показан без сжатия. Толщина панели и шляпки, отверстие панели и выступ кнопки — условно.',
         fontsize=10.5,color=MUTED)

for ext in ['png','svg']:
    fig.savefig(OUT/f'damper_01_H5_section.{ext}',dpi=200,facecolor='white')
meta = {'revision':'drawing-only H5; fit correction pending measurement',
        'units':'mm','prototype':'01_reference','free_height':H,
        'foot_inner_diameter':2*RI,'foot_outer_diameter':2*RO,'foot_height':FOOT_H,
        'cone_upper_outer_diameter':2*RTOP,'wall_normal_thickness':.70,
        'root_normal_thickness':.85,'root_fillet_radius':.15,
        'root_transition_height':ROOT_TRANSITION,
        'button_central_diameter_previous_measurement':2*SHAFT_R,
        'button_head_diameter_previous_measurement':2*HEAD_R,
        'printed_bore_diameter':None,'step_exported':False,
        'solid_valid':solid.isValid(),'solid_count':len(solid.Solids()),
        'height_checked':bb.zlen,'outer_diameter_checked':bb.xlen}
(OUT/'dimensions.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(meta,ensure_ascii=False,indent=2))
print(OUT/'damper_01_H5_section.png')
