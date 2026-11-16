"""Build current assembly PDFs from PCB geometry and BOM.csv. Requires reportlab and PyMuPDF."""
import re,json
from pathlib import Path
def parse(path):
 stack=[];root=None
 for m in re.finditer(r'"(?:\\.|[^"\\])*"|[()]|[^()\s]+',Path(path).read_text()):
  t=m.group()
  if t=='(':
   node=[]
   if stack:stack[-1].append(node)
   else:root=node
   stack.append(node)
  elif t==')':stack.pop()
  else:stack[-1].append(json.loads(t) if t.startswith('"') else t)
 return root
def children(n,k):return [a for a in n if isinstance(a,list) and a and a[0]==k]
def get(n,k,default=None):return next(iter(children(n,k)),default)

import csv,math,hashlib,io,collections,datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4,landscape
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor,Color,white
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph,Table,TableStyle
from reportlab.lib.styles import ParagraphStyle
from xml.sax.saxutils import escape
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'doc/assembly-notes'
DATE='16.11.2026'
for name,file in [('D','DejaVuSans.ttf'),('DB','DejaVuSans-Bold.ttf')]:
 pdfmetrics.registerFont(TTFont(name,'/usr/share/fonts/truetype/dejavu/'+file))
W,H=landscape(A4); M=11*mm
INK=HexColor('#202c38');ACC=HexColor('#006c9b');FAINT=HexColor('#ccd1d5')
PS=ParagraphStyle('body',fontName='D',fontSize=9,leading=13,textColor=INK,spaceAfter=7)
SM=ParagraphStyle('small',parent=PS,fontSize=8,leading=11)
board=parse(ROOT/'640A_PowerAmp.kicad_pcb')
fps={}
for fp in children(board,'footprint'):
 props={p[1]:p[2] for p in children(fp,'property')}
 ref=props['Reference'];fps[ref]=fp
rows=list(csv.DictReader((ROOT/'BOM.csv').open(encoding='utf-8-sig'),delimiter=';'))
bom={}
for row in rows:
 for ref in row['Обозначения'].split(', '):
  if ref in fps and row['Раздел']!='Ответные части разъёмов':bom[ref]=row
installed={ref for ref,row in bom.items() if 'DNP' not in row['Примечание'] and row['Подраздел']!='Площадки без деталей'}
assert len(installed)==274,len(installed)
PCB_HASH=hashlib.sha256((ROOT/'640A_PowerAmp.kicad_pcb').read_bytes()).hexdigest()
def order(ref):return (re.match('[A-Z]+',ref).group(),int(re.search(r'\d+',ref).group()))
def at(n):
 a=get(n,'at',['at','0','0']);return float(a[1]),float(a[2]),float(a[3]) if len(a)>3 else 0

def global_xy(fp,x,y):
 ox,oy,deg=at(fp);t=math.radians(deg)
 return ox+x*math.cos(t)+y*math.sin(t),oy-x*math.sin(t)+y*math.cos(t)
def xy(n,k):return tuple(map(float,get(n,k)[1:3]))
def geom(fp):
 shapes=[x for x in fp if isinstance(x,list) and x and x[0] in ['fp_line','fp_rect','fp_circle','fp_arc','fp_poly'] and get(x,'layer')==['layer','F.Fab']]
 if not shapes:shapes=[x for x in fp if isinstance(x,list) and x and x[0] in ['fp_line','fp_rect','fp_circle','fp_arc','fp_poly'] and get(x,'layer')==['layer','F.SilkS']]
 return shapes

def line_points(g):
 kind=g[0]
 if kind in ['fp_line','gr_line']:return [xy(g,'start'),xy(g,'end')]
 if kind in ['fp_rect','gr_rect']:
  (x,y),(a,b)=xy(g,'start'),xy(g,'end');return [(x,y),(a,y),(a,b),(x,b),(x,y)]
 if kind in ['fp_poly','gr_poly']:
  pts=[tuple(map(float,p[1:3])) for p in children(get(g,'pts'),'xy')];return pts+[pts[0]]
 if kind in ['fp_circle','gr_circle']:
  x,y=xy(g,'center');a,b=xy(g,'end');rad=math.hypot(a-x,b-y)
  return [(x+rad*math.cos(i*math.tau/60),y+rad*math.sin(i*math.tau/60)) for i in range(61)]
 if kind in ['fp_arc','gr_arc']:
  (ax,ay),(bx,by),(cx,cy)=xy(g,'start'),xy(g,'mid'),xy(g,'end')
  d=2*(ax*(by-cy)+bx*(cy-ay)+cx*(ay-by))
  if abs(d)<1e-8:return [(ax,ay),(bx,by),(cx,cy)]
  ux=((ax*ax+ay*ay)*(by-cy)+(bx*bx+by*by)*(cy-ay)+(cx*cx+cy*cy)*(ay-by))/d
  uy=((ax*ax+ay*ay)*(cx-bx)+(bx*bx+by*by)*(ax-cx)+(cx*cx+cy*cy)*(bx-ax))/d
  aa,bb,cc=[math.atan2(y-uy,x-ux) for x,y in [(ax,ay),(bx,by),(cx,cy)]]
  sweep=(cc-aa)%math.tau
  if (bb-aa)%math.tau>sweep:sweep-=math.tau
  rad=math.hypot(ax-ux,ay-uy)
  return [(ux+rad*math.cos(aa+sweep*i/40),uy+rad*math.sin(aa+sweep*i/40)) for i in range(41)]
 return []

PADS={}
for ref,fp in fps.items():
 PADS[ref]=[]
 for p in children(fp,'pad'):
  px,py,_=at(p);x,y=global_xy(fp,px,py)
  PADS[ref].append({'number':p[1],'x':x,'y':y,'net':(get(p,'net') or ['net',''])[ -1 ],'shape':p[3],'size':list(map(float,get(p,'size')[1:3]))})

def page(c,title,subtitle='Текущая PCB • Вид со стороны компонентов • Без медной разводки'):
 c.setFillColor(INK);c.setFont('DB',15);c.drawString(M,H-17*mm,title)
 c.setFont('D',8);c.drawString(M,H-23*mm,subtitle)
 c.setStrokeColor(FAINT);c.line(M,13*mm,W-M,13*mm)
 c.setFont('D',7);c.drawString(M,9*mm,f'Cambridge 640A V1 | {DATE} | PCB SHA-256: {PCB_HASH[:16]}')
 c.drawRightString(W-M,9*mm,str(c.getPageNumber()))

def paragraph(c,text,x,y,width,style=PS):
 p=Paragraph(text,style);_,h=p.wrap(width,1000);p.drawOn(c,x,y-h);return y-h-6

def text_page(c,title,paras,table=None):
 page(c,title,'Текущая PCB и BOM.csv • Документы по сборке • '+DATE);y=H-34*mm
 for text in paras:
  if y<35*mm:c.showPage();page(c,title+' — продолжение');y=H-34*mm
  y=paragraph(c,text,M,y,W-2*M)
 if table:
  widths=[(W-2*M)*f for f in ([.11,.28,.17,.44] if len(table[0])==4 else [.18,.82])]
  index=1
  while index<len(table):
   count=min(7,len(table)-index)
   while True:
    data=[[Paragraph(escape(str(v)),SM) for v in row] for row in [table[0]]+table[index:index+count]]
    t=Table(data,colWidths=widths,hAlign='LEFT')
    t.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('BACKGROUND',(0,0),(-1,0),HexColor('#e5eff4')),('LINEBELOW',(0,0),(-1,0),.6,ACC),('BOTTOMPADDING',(0,0),(-1,-1),5),('TOPPADDING',(0,0),(-1,-1),4),('LINEBELOW',(0,1),(-1,-1),.2,FAINT)]))
    _,h=t.wrap(W-2*M,1000)
    if h<=y-22*mm:break
    if count>1:count-=1;continue
    if y>=H-34*mm-1:raise ValueError('Oversized table row: '+title)
    c.showPage();page(c,title+' — продолжение');y=H-34*mm
   t.drawOn(c,M,y-h);y-=h+8;index+=count
   if index<len(table):c.showPage();page(c,title+' — продолжение');y=H-34*mm
 c.showPage()

# Consistent plotting area includes complete SAP15 bodies above the board edge.
VIEW=(46.,26.,253.,182.)
def draw_map(c,selected=None,pins=False,region=None,base=False):
 if selected is not None and not base:
  form="base-"+str(region)
  if not hasattr(c,"assembly_forms"):c.assembly_forms=set()
  if form not in c.assembly_forms:
   c.beginForm(form);draw_map(c,set(),region=region,base=True);c.endForm();c.assembly_forms.add(form)
  c.doForm(form)
 x0,y0,x1,y1=region or VIEW
 scale=min((W-2*M)/((x1-x0)*mm),(H-48*mm)/((y1-y0)*mm))*mm
 left=(W-(x1-x0)*scale)/2;top=H-29*mm
 def pos(x,y):return left+(x-x0)*scale,top-(y-y0)*scale
 c.saveState();clip=c.beginPath();clip.rect(left,top-(y1-y0)*scale,(x1-x0)*scale,(y1-y0)*scale);c.clipPath(clip,stroke=0)
 for g in board:
  if not isinstance(g,list) or not g or get(g,'layer')!=['layer','Edge.Cuts']:continue
  pts=line_points(g)
  if pts:
   c.setStrokeColor(INK);c.setLineWidth(.4);p=c.beginPath();p.moveTo(*pos(*pts[0]))
   for pt in pts[1:]:p.lineTo(*pos(*pt))
   c.drawPath(p)
 for ref,fp in fps.items():
  if selected is not None and not base and ref not in selected:continue
  active=selected is None or ref in selected
  color=INK if selected is None else ACC if active else FAINT
  c.setStrokeColor(color);c.setFillColor(color);c.setLineWidth(.4 if active else .22)
  for g in geom(fp):
   pts=line_points(g)
   if not pts:continue
   p=c.beginPath();p.moveTo(*pos(*global_xy(fp,*pts[0])))
   for pt in pts[1:]:p.lineTo(*pos(*global_xy(fp,*pt)))
   c.drawPath(p)
  for pad in PADS[ref]:
   x,y=pos(pad['x'],pad['y']);diam=min(pad['size'])*scale*.65
   # Outline symbol marks the hole/pin location; it is not a copper manufacturing plot.
   if pad['number']=='1' and pad['shape'] in ['rect','roundrect']:
    c.rect(x-diam/2,y-diam/2,diam,diam,fill=0,stroke=1)
   else:c.circle(x,y,diam/2,fill=0,stroke=1)
  for prop in children(fp,'property'):
   if prop[1]!='Reference':continue
   x,y,_=at(prop);gx,gy=global_xy(fp,x,y)
   c.setFont('DB' if active else 'D',max(3.4,.88*scale));c.drawCentredString(*pos(gx,gy),ref)
  if ref in ['C16','C44']:
   x,y=pos(*at(fp)[:2]);c.setStrokeColor(HexColor('#a02a60'));c.line(x-2*scale,y-2*scale,x+2*scale,y+2*scale);c.line(x-2*scale,y+2*scale,x+2*scale,y-2*scale)
  if pins and active and ref.startswith('CN'):
   for pad in PADS[ref]:
    x,y=pos(pad['x'],pad['y']);c.setFillColor(ACC);c.circle(x,y,1.3*scale,stroke=0,fill=1);c.setFillColor(white);c.setFont('DB',1.5*scale);c.drawCentredString(x,y-.5*scale,pad['number'])
 c.restoreState()

def map_page(c,title,selected=None,subtitle=None,pins=False,region=None):
 page(c,title,subtitle or 'Синим выделены позиции этапа; остальные — серым. C16/C44: DNP. Без медной разводки.')
 draw_map(c,selected,pins,region);c.showPage()

def new_pdf(path):
 path.parent.mkdir(parents=True,exist_ok=True)
 c=canvas.Canvas(str(path),pagesize=landscape(A4),pageCompression=1,invariant=1)
 c.setTitle('Cambridge 640A — '+path.stem+' — текущая PCB');c.setAuthor('Cambridge 640A project');return c

NAMES=['Малые резисторы и диоды','Резисторы 0,25–0,66 Вт и 1N4004','Микросхемы DIP-8','Низкая керамика и плёнка','Вертикальные резисторы R120/R121','Транзисторы TO-92','Выпрямительный мост и мощные резисторы','Крупная плёнка и подстроечники','Малые электролиты','Разъёмы JST XH/VH','TO-126 и стабилизаторы','Крупные электролиты','Выходной каскад и провод J4']
STEPS={i:[] for i in range(1,14)}
for ref in sorted(installed,key=order):
 row=bom[ref];fp=fps[ref];foot=fp[1];cat=row['Раздел'];sub=row['Подраздел']
 if ref in ['R120','R121']:step=5
 elif ref.startswith('R'):
  if sub=='Подстроечные':step=8
  elif row['Мощность, Вт']=='3':step=7
  elif row['Мощность, Вт']=='0,125':step=1
  else:step=2
 elif ref.startswith('D'):step=7 if ref in ['D17','D18','D19','D20'] else 2 if row['Номинал']=='1N4004' else 1
 elif ref in ['U1','U6','U7']:step=3
 elif ref.startswith('C'):
  if 'Электролитические' in sub:
   diameter=float(re.search(r'D([0-9.]+)mm',foot).group(1));step=12 if diameter>=10 else 9
  else:step=8 if ref in ['C18','C39','C46','C48'] else 4
 elif ref.startswith('CN'):step=10
 elif ref.startswith('Q'):step=13 if ref=='Q20' else 11 if 'TO-126' in foot else 6
 elif ref in ['U8','U9','U10']:step=11
 elif ref in ['U2','U3','U4','U5']:step=13
 else:raise AssertionError(ref)
 STEPS[step].append(ref)
STEPS[13].append('J4')
assert len(set(sum(STEPS.values(),[])) - {'J4'})==274
assert 'C70' in STEPS[12] and 'R122' in STEPS[2]
NOTES={
1:['Подобрать парные резисторы до пайки: R30/R31, R80/R81, R14/R15, R58/R59, R34/R79; группа 33 кОм — R36/R82/R102/R65 (R102/R65 устанавливаются на шаге 2). Сопротивление щупов учесть при сравнении малых номиналов.','Полосу диода совместить с катодом по маркировке и выводу K в схеме; не определять полярность только по форме площадки. Проверить каждую из D21–D28 отдельно.'],
2:['R41/R43/R96/R98: 150 Ом, 0,5 Вт, огнестойкое fusible-исполнение по BOM. R88: 11 кОм, 0,25 Вт.','R122/R123 в текущей PCB стоят лёжа с шагом 10,16 мм: 47 Ом, 0,5 Вт. Это исходный номинал RC-снабберов; окончательный подбор по измерениям звона. Перенесены из прежнего этапа вертикальных резисторов.'],
3:['U1/U6 — NE5534, U7 — LM393. Вывод 1 и ключ сверить со схемой и корпусом. До пайки примерить соседние C3/C52: панельки U1/U7 могут мешать их установке.'],
4:['C16/C44 — DNP: не устанавливать. C81 отсутствует в текущей PCB. Ёмкости и напряжения брать из таблицы этапа и BOM.','Формованные выводы керамики не продавливать за заводской изгиб. Проверить отсутствие замыкания между соседними площадками после пайки.'],
5:['Только R120/R121: 100 Ом, 0,25 Вт, 1 %, вертикальная посадка с шагом 2,54 мм. Не использовать прежние 0,125 Вт из старой инструкции.','R122/R123 монтируются лёжа на шаге 2. TP1–TP6 — измерительные площадки, покупные детали для них не нужны.'],
6:['Подобранные пары: Q7/Q8 и Q28/Q29 — MPSA92/93; Q9/Q10 и Q26/Q27 — MPSA42/43. Измерять в одинаковых условиях до монтажа. В прежнем подборе цели: hFE в пределах 5–10 %, Vbe в пределах 2–3 мВ.','Номера экземпляров из прежней личной партии не назначаются новым деталям автоматически. Цоколёвку сверять с документацией именно установленного производителя: BC327/337 и MPSA могут различаться.'],
7:['D17–D20: BY550-400, не SB5200 из ранней инструкции. Проверить катоды до пайки.','R44/R50: 4,7 Ом, 3 Вт; зазор около 3 мм над платой. R22/R52/R69/R100: 0,22 Ом, 3 Вт. Установить до крупных электролитов, сохранив доступ к пайке.'],
8:['C18/C39: 2,2 мкФ, 100 В, WIMA MKS2 по BOM. C46/C48: 100 нФ, 160 В Poly по текущему BOM.','R68/R116: 47 Ом, 0,5 Вт по BOM. До включения выставить положение минимального тока покоя по отдельной инструкции запуска; не определять его только по направлению вращения.'],
9:['C13/C47 и C17/C41 — неполярные NP/BP. C13/C47 и C22/C42: Ø8 мм, шаг 3,5 мм. Полярные электролиты ориентировать по маркировке плюса и схеме.','C70/C71/C74/C75 теперь Ø10 мм, шаг 5 мм: они перенесены на шаг 12. Не использовать старые карты с Ø8 и прежним шагом.'],
10:['CN20/CN21 — JST VH, 3 контакта, шаг 3,96 мм. CN23/CN24 — VH, 2 контакта. CN21 XH из ранних PDF к текущей PCB не относится.','Остальные разъёмы: XH по BOM. Припаять один вывод, проверить посадку и ключ, затем остальные. Нумерацию жгута сверить с обновлённым документом подключения; вид в ответную колодку зеркален.'],
11:['U8 — 7805, U9 — 7815, U10 — 7915. TRACO TSR и C81 не устанавливаются. Все три стабилизатора монтируются с изолирующими прокладками, втулками крепежа и термопастой по BOM.','До пайки примерить радиатор, проверить электрическую изоляцию крепежа и выводов. Для MJE340/MJE350 сверить цоколёвку и ориентацию по схеме и документации производителя.'],
12:['Соблюдать полярность каждой позиции. C70/C71/C74/C75: Ø10 мм, шаг 5 мм. Основной банк 2200 мкФ: C21/C23/C25/C26/C29/C30/C62/C63 (8 штук).','До пайки проверить высоту, формовку выводов и зазоры в корпусе. Переносимые электролиты проверить по состоянию и параметрам. Банк 2200 мкФ устанавливать последним из конденсаторов.'],
13:['U2/U4 — SAP15P, U3/U5 — SAP15N; Q20 — MJE340. Сначала примерить радиатор и крепёж, затем паять выводы без механического натяга. Использовать предусмотренные изоляторы и термопасту.','J4 — один провод к корпусу, отдельная покупная деталь для площадки не нужна. J4 связан с PGND через R97 47 Ом параллельно C31 100 нФ; не заменять эту цепь прямым проводом.']}

def bom_table(refs):
 groups=collections.OrderedDict()
 for ref in sorted(refs,key=order):
  row=bom[ref];key=(row['Номинал'],row['Мощность, Вт'],row['Корпус / посадка']);groups.setdefault(key,[]).append(ref)
 return [['Позиции','Номинал','Мощность, Вт','Корпус / посадка']]+[[', '.join(refs),*key] for key,refs in groups.items()]

def build():
 OUT.mkdir(parents=True,exist_ok=True)
 c=new_pdf(OUT/'640A_PowerAmp_v2_assembly_instructions.pdf')
 text_page(c,'Порядок сборки — текущая ревизия',[
 'Карты построены заново по координатам, поворотам, контурам корпусов и площадкам текущего файла 640A_PowerAmp.kicad_pcb. Номиналы, мощности и DNP взяты из BOM.csv. Старые монтажные картинки не используются.',
 '13 этапов сохраняют общий порядок от низких деталей к высоким. Из-за новых корпусов R122/R123 перенесены на этап 2, C70/C71/C74/C75 — на этап 12. На каждой карте синим выделены позиции этапа; медная разводка не показана.',
 'Один комплект карт относится к текущим исходникам. На уже изготовленной ранней плате расположение и посадки могут отличаться; сверить маркировку и размеры перед использованием.',
 'До пайки проверить комплектность и подобрать парные детали. Не считать отметки в прежней инструкции подтверждением установки на этой плате.'],[['Этап','Группа']]+[[str(i),f'{NAMES[i-1]} — {len(STEPS[i])} поз.'] for i in STEPS])
 for step,refs in STEPS.items():
  title=f'{step:02d}. {NAMES[step-1]}'
  map_page(c,title,refs)
  text_page(c,title+' — монтаж',NOTES[step]+['Чек-лист: '+ '  '.join('□ '+r for r in refs)],bom_table(refs))
 text_page(c,'Проверка перед первым включением',[
 '□ Проверить полярности, ориентацию микросхем и транзисторов, пайку и отсутствие перемычек припоя.',
 '□ Проверить изоляцию силовых элементов и стабилизаторов от радиаторов. Проверить настройку подстроечников на минимальный ток покоя по инструкции запуска.',
 '□ Сверить кабели и нумерацию: CN23 — левый канал (RO), CN24 — правый (LO). Проверить связь корпуса через J4 и R97/C31.',
 'Первое включение и настройка выполняются по doc/v2/FIRST_POWER_UP_V2.md (также PDF). Эта инструкция содержит порядок монтажа; она не заменяет процедуру запуска.'])
 c.save()
 c=new_pdf(ROOT/'doc/640A_PowerAmp_v2_assembly_order.pdf')
 text_page(c,'Порядок сборки — 13 этапов',[
 'Краткие карты очередности монтажа для текущего размещения. Подробные указания, номиналы и чек-листы — в doc/assembly-notes/640A_PowerAmp_v2_assembly_instructions.pdf.'],[['Этап','Группа']]+[[str(i),NAMES[i-1]] for i in STEPS])
 for step,refs in STEPS.items():map_page(c,f'{step:02d}. {NAMES[step-1]}',refs)
 c.save()
 c=new_pdf(OUT/'640A_PowerAmp_v2_resistors_by_value.pdf')
 resistors=collections.OrderedDict()
 for row in rows:
  if row['Раздел']=='Резисторы':
   key=(row['Номинал'],row['Мощность, Вт'],row['Подраздел'])
   resistors.setdefault(key,[]).extend(row['Обозначения'].split(', '))
 text_page(c,'Резисторы — номиналы и мощности',[
 'Карта каждой группы построена по текущей PCB; номиналы и мощности — по BOM.csv. Подстроечники включены отдельной группой. Одинаковые номиналы с разными посадками выделяются на одной карте, фактические посадки перечислены в указателе.',
 'R88: 11 кОм, 0,25 Вт; R120/R121: 100 Ом, 0,25 Вт, вертикально; R122/R123: 47 Ом, 0,5 Вт, лёжа; R44/R50: 4,7 Ом, 3 Вт.'],[['Группа','Позиции / посадки']]+[[f'{val} / {power} Вт',', '.join(refs)+'; '+'; '.join(sorted({bom[r]['Корпус / посадка'] for r in refs}))] for (val,power,sub),refs in resistors.items()])
 for (val,power,sub),refs in resistors.items():
  map_page(c,f'{val} / {power} Вт — '+('подстроечники' if sub=='Подстроечные' else f'{len(refs)} шт.'),refs,', '.join(refs)+' | Синим — только эта группа. Отметить после проверки монтажа.')
 c.save()
 c=new_pdf(ROOT/'doc/640A_PowerAmp_v2_assembly.pdf')
 map_page(c,'Монтажный план — текущая PCB',None,'Полные контуры F.Fab, площадки и обозначения текущей PCB. Медная разводка не показана.')
 map_page(c,'Монтажный план — левый канал',None,'Вид сверху; увеличенный фрагмент текущей PCB.',region=(48,26,148,180))
 map_page(c,'Монтажный план — правый канал',None,'Вид сверху; увеличенный фрагмент текущей PCB.',region=(148,26,251,180))
 text_page(c,'Монтажные особенности текущей ревизии',[
 'C13/C47 и C22/C42: Ø8 мм, шаг 3,5 мм; C70/C71/C74/C75: Ø10 мм, шаг 5 мм. C13/C47 и C17/C41 — неполярные.',
 'CN20/CN21 и CN23/CN24: JST VH. Нумерацию контактов и цвета проводов смотреть в документе подключения текущей ревизии.',
 'U8=7805, U9=7815, U10=7915: изоляционные комплекты по BOM. C81 отсутствует. C16/C44 — DNP.',
 'R88: 11 кОм / 0,25 Вт. R120/R121: вертикально, 100 Ом / 0,25 Вт. R122/R123: лёжа, 47 Ом / 0,5 Вт. R44/R50: 4,7 Ом / 3 Вт, зазор около 3 мм.',
 'TP1–TP6 — площадки без покупных деталей. J4 — провод к корпусу через предусмотренную цепь R97/C31. NT1–NT3 — медь платы.',
 'Подробный порядок: doc/assembly-notes/640A_PowerAmp_v2_assembly_instructions.pdf. Перечень деталей: BOM.md / BOM.csv. Первое включение: doc/v2/FIRST_POWER_UP_V2.md.'])
 c.save()
 build_wiring()
 manifest={'date':'2026-11-16','pcb_sha256':PCB_HASH,'bom_sha256':hashlib.sha256((ROOT/'BOM.csv').read_bytes()).hexdigest(),'generator':'scripts/build_assembly_docs.py','geometry':'PCB F.Fab outlines, pad centres, current reference positions; no tracks or zones','steps':{str(k):v for k,v in STEPS.items()},'installed_positions':len(installed),'DNP':['C16','C44'],'pads_without_parts':['J4']+[f'TP{i}' for i in range(1,7)],'position_check':{ref:{'at':list(at(fps[ref])),'pads':PADS[ref]} for ref in sorted(bom,key=order)}}
 (OUT/'source.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')

WIRE={'CN20': [('1','Жёлтый','Вторичная обмотка'),('2','Красный','Вторичная обмотка'),('3','Оранжевый','Средняя точка, PGND')], 'CN21':[('1','Зелёный','Вспомогательная обмотка'),('2','Фиолетовый','Средняя точка, AUX0V'),('3','Серый','Вспомогательная обмотка')], 'CN23':[('1','Красный','Левый выход, RO'),('2','Чёрный','Возврат АС, PGND')], 'CN24':[('1','Красный','Правый выход, LO'),('2','Чёрный','Возврат АС, PGND')]}

def build_wiring():
 refs=list(WIRE)+['J4']
 for path,compact in [(ROOT/'doc/640A_PowerAmp_v2_wiring.pdf',False),(OUT/'640A_power_connector_wire_colors.pdf',True)]:
  c=new_pdf(path);map_page(c,'Подключение платы — текущая ревизия',refs,'Вид сверху. Положения и номера площадок взяты из PCB. Все четыре выделенных разъёма — JST VH.',pins=True)
  text_page(c,'Контакты и цвета проводов',[
   'Номера на карте показывают контакт на плате, вид со стороны деталей. Вид в ответную колодку зеркален. Ориентироваться по номеру контакта и ключу; не по порядку цветов слева направо на старом рисунке.',
   'CN20: средняя точка — контакт 3. CN21: средняя точка — контакт 2. Красный/чёрный на выходах — принятая маркировка жгута проекта. Цвета обмоток соответствуют зафиксированной проводке аппарата.',
   'J4 соединён с PGND через R97 47 Ом параллельно C31 100 нФ. Не шунтировать эту цепь прямым соединением PGND с корпусом.'],[['Разъём','Контакт / цвет','Сеть / назначение','Координаты площадки X / Y, мм']]+[[ref,f'{num} — {color}',function,f'{pad["x"]:.3f} / {pad["y"]:.3f}'] for ref,pins in WIRE.items() for num,color,function in pins for pad in PADS[ref] if pad['number']==num])
  if not compact:text_page(c,'Сборка и проверка жгута',[
   '1. При отключённом аппарате промаркировать каждый провод перед снятием старой платы. Цвета на заводской схеме могут отличаться от проводки конкретного аппарата; прозвонить назначение проводов.',
   '2. CN20/CN21: корпуса VHR-3N. CN23/CN24: VHR-2N. Контакты SVH-21T-P1.1 по BOM; провод и обжим выбирать в пределах спецификации контакта. XH и VH не взаимозаменяемы.',
   '3. Обжать контакты подходящим инструментом, проверить удержание провода и фиксацию контактов в корпусе. Сверить номер каждого гнезда с ключом ответной колодки и площадкой 1 на плате.',
   '4. Прозвонить каждую жилу от корпуса разъёма до точки назначения. CN23 — левый выход, CN24 — правый; оба возврата — PGND. Проверить отсутствие непредусмотренных соединений с корпусом.',
   '5. Перед подачей питания проверить средние точки CN20.3 и CN21.2, полярности, пайку и изоляцию радиаторов. Далее следовать doc/v2/FIRST_POWER_UP_V2.md / .pdf. Не включать плату только по этому документу проводки.'])
  c.save()
 import fitz
 pdf=fitz.open(OUT/'640A_power_connector_wire_colors.pdf')
 pdf[0].get_pixmap(matrix=fitz.Matrix(2,2)).save(OUT/'640A_power_connector_wire_colors.png')

if __name__=='__main__':build();print('Generated current assembly documents: 274 installed positions; 13 steps; geometry from PCB')
