"""Generate the single-table Markdown BOM and Excel workbook from BOM.csv."""
from pathlib import Path
import csv,re
from openpyxl import Workbook
from openpyxl.styles import Font,PatternFill,Alignment,Border,Side
from openpyxl.worksheet.table import Table,TableStyleInfo
from openpyxl.worksheet.pagebreak import Break
ROOT=Path(__file__).resolve().parents[1]
rows=list(csv.DictReader((ROOT/'BOM.csv').open(encoding='utf-8-sig'),delimiter=';'));fields=list(rows[0])
intro='''# BOM — Cambridge 640A, текущий проект следующего изготовления

[**Скачать Excel (.xlsx)**](https://github.com/SSSound13/Cambridge_640A_PowerAmp/raw/refs/heads/main/BOM.xlsx) · [Скачать CSV](BOM.csv)

Одна таблица для всей платы и ответных частей разъёмов. Резисторы сгруппированы по мощности; внутри каждой группы номиналы идут по возрастанию. Одинаковые детали с разными посадками или статусом добавления показаны отдельными строками.

**«+» — только элементы, добавленные относительно заводской платы.** Замены штатных деталей и увеличенные посадки плюсом не отмечаются. Например, C79/C80 имеют «+», C24/C28 — нет.

Всего на плате **283 позиции**: 274 устанавливаемые детали, 2 DNP (C16/C44), 7 площадок без покупных деталей (TP1–TP6 и J4). NT1–NT3 — медь платы, не покупные детали. Ещё 14 единиц ответных частей разъёмов перечислены отдельно в конце той же таблицы.

Параметры посадок — для [текущего проекта](doc/v2/NO_VIAS.md). На изготовленной v2 остаются прежние посадки и CN21 XH. Мощности штатных резисторов сверены с [заводским BOM, стр. 23](doc/Cambridge_Azur_640A_V1_Service_Manual_AP14676-1.pdf): в частности, **R88 — 1/4 Вт**, R53/R64/R67/R103 — **1/8 Вт**. У R68/R116 мощность 0,5 Вт, отдельная подгруппа «Подстроечные».

'''
old=(ROOT/'BOM.md').read_text();footer=old[old.index('## Сборка:'):].replace('— не меньше 13 мВ.','— более 13 мВ по мануалу; порядок настройки см. [инструкцию](doc/v2/FIRST_POWER_UP_V2.md).')
def esc(s):return str(s).replace('|','\\|').replace('\n',' ')
md=intro+'| '+' | '.join(fields)+' |\n| '+' | '.join('---:' if f=='Кол-во' else ':---:' if f=='+' else '---' for f in fields)+' |\n'
md+='\n'.join('| '+' | '.join(esc(r[f]) for f in fields)+' |' for r in rows)+'\n\n'+footer
(ROOT/'BOM.md').write_text(md)
wb=Workbook();ws=wb.active;ws.title='BOM'
ws['A1']='Cambridge 640A — единый BOM';ws['A1'].font=Font(size=18,bold=True,color='17365D')
ws['A2']='+ = только добавленные относительно заводской платы элементы; замены штатных без плюса.'
ws['A3']='Резисторы: мощность по группам, сопротивление по возрастанию. Фильтры включены.'
ws['A4']='283 позиции PCB + 14 единиц ответных частей жгута. DNP и площадки без деталей отмечены в примечаниях.'
ws['A5']='Текущий проект: CN21 VH. На изготовленной v2 остаётся XH; посадки отличаются.'
ws['A6']='Источник: BOM.csv; мощности штатных резисторов — сервис-мануал, стр. 23. R88: 1/4 Вт.'
for i in range(2,7):ws.cell(i,1).font=Font(size=10,color='555555')
ws.append(fields)
last=None
for idx,r in enumerate(rows,8):
 values=[]
 for f in fields:
  v=r[f]
  if f=='Кол-во':v=int(v)
  elif f=='Мощность, Вт' and v:v=float(v.replace(',','.'))
  else:v=re.sub(r'\[([^]]+)\]\([^)]+\)',r'\1',v)
  values.append(v)
 ws.append(values)
 key=(r['Раздел'],r['Подраздел']);newgroup=key!=last
 for c in ws[idx]:
  c.alignment=Alignment(vertical='top',wrap_text=True)
  c.font=Font(name='Calibri',size=11)
  if newgroup:c.border=Border(top=Side(style='medium',color='8497B0'))
 if newgroup:
  for col in [1,2]:ws.cell(idx,col).fill=PatternFill('solid',fgColor='D9E5F2');ws.cell(idx,col).font=Font(bold=True,color='17365D')
 if r['+']:ws.cell(idx,9).fill=PatternFill('solid',fgColor='C6E0B4');ws.cell(idx,9).font=Font(bold=True,color='215E21',size=14)
 ws.cell(idx,9).alignment=Alignment(horizontal='center',vertical='top')
 ws.cell(idx,10).number_format='@';ws.row_dimensions[idx].height=62 if len(r['Примечание'])<160 else 90
 last=key
end=7+len(rows);table=Table(displayName='CambridgeBOM',ref=f'A7:K{end}');table.tableStyleInfo=TableStyleInfo(name='TableStyleMedium2',showRowStripes=True);ws.add_table(table)
for c in ws[7]:c.font=Font(bold=True,color='FFFFFF');c.fill=PatternFill('solid',fgColor='17365D');c.alignment=Alignment(wrap_text=True,vertical='center')
ws.row_dimensions[7].height=32
for col,width in zip('ABCDEFGHIJK',[22,25,9,40,31,13,43,48,5,19,76]):ws.column_dimensions[col].width=width
ws.freeze_panes='E8';ws.sheet_view.zoomScale=75;ws.sheet_properties.pageSetUpPr.fitToPage=True
ws.page_setup.orientation='landscape';ws.page_setup.paperSize=ws.PAPERSIZE_A3;ws.page_setup.fitToWidth=1;ws.page_setup.fitToHeight=0
ws.print_title_rows='7:7';ws.print_area=f'A7:K{end}';ws.oddFooter.center.text='Cambridge 640A — BOM';ws.oddFooter.right.text='&P / &N'
wb.save(ROOT/'BOM.xlsx')
print(f'Generated BOM.md and BOM.xlsx: {len(rows)} rows, one table')
