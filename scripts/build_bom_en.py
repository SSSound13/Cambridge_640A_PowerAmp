"""Generate the English BOM from the authoritative BOM.csv; retain all positions and values."""
from pathlib import Path
import csv,re
ROOT=Path(__file__).resolve().parents[1]
NOTES={
'Вне платы; силовые жгуты AWG16 (около 1,25 мм²). Номинал JST VH 10 А указан для AWG16; контакт SVH-41T.':'Off-board; power harnesses AWG16 (about 1.25 mm²). JST rates VH at 10 A with AWG16; use SVH-41T contacts.',
'Вне платы; вспомогательная обмотка, провод AWG18 (около 0,83 мм²), контакт SVH-21T.':'Off-board; auxiliary winding, AWG18 wire (about 0.83 mm²), SVH-21T contacts.',
'1%, металлоплёночный.':'1%, metal film.',
'1%, металлоплёночный; 1/4 Вт по заводскому BOM.':'1%, metal film; 1/4 W per factory BOM.',
'1%, металлоплёночный; заводской BOM, стр. 23':'1%, metal film; factory BOM, page 23.',
'1%. Добавлено: ограничение сопротивления цепи регулировки тока покоя.':'1%. Added to limit bias-adjustment resistance.',
'C7/C33/C43/C66 желательно на 63 В':'63 V preferred for C7/C33/C43/C66.',
'DNP — не устанавливать. не устанавливать (DNP), место под коррекцию на случай возбуждения':'DNP — do not fit; compensation positions reserved in case of oscillation.',
'Sanken SAP15; монтаж на радиатор с изоляцией.':'Sanken SAP15; insulated heatsink mounting.',
'Вне платы; количество отдельно от позиций PCB.':'Off-board; quantity counted separately from PCB positions.',
'Вспомогательная вторичная обмотка; JST VH.':'Auxiliary secondary winding; JST VH.',
'Выбирать корпус и формовку выводов под указанную посадку.':'Choose the body and lead forming to match this footprint.',
'Добавлено: конденсаторы RC-снабберов вторичной обмотки.':'Added: secondary-winding RC snubber capacitors.',
'Добавлено: снабберы; 47 Ом — стартовый номинал, подбор по звону вторичной обмотки.':'Added snubbers; 47 ohm is the initial value, adjusted by secondary-winding ringing measurements.',
'Замена штатной детали.':'Replacement for the factory part.',
'Замена штатных конденсаторов цепей Цобеля.':'Replacement for factory Zobel capacitors.',
'Изолирующая прокладка, втулка крепежа и термопаста.':'Insulating pad, mounting bushing and thermal compound.',
'Огнестойкий (fusible), 150 Ом / 0,5 Вт. Замена штатной детали.':'Flameproof fusible, 150 ohm / 0.5 W. Replacement for factory part.',
'Площадка без покупной детали. клемма связи PGND с корпусом (провод на стойку), деталь не нужна':'Pad without purchased part; chassis wire to mounting post through the PGND/chassis network.',
'Площадка без покупной детали. контрольные точки для настройки тока покоя, деталь не нужна':'Pad without purchased part; bias-adjustment test point.',
'Посадка Ø8 мм, шаг 3,5 мм.':'Footprint Ø8 mm, 3.5 mm pitch.',
'Проволочный.':'Wirewound.',
'Проволочный; установить с зазором около 3 мм над платой.':'Wirewound; mount about 3 mm above PCB.',
'Увеличенная посадка текущего проекта.':'Enlarged footprint in current revision.',
'изоляционный комплект и термопаста':'Insulation kit and thermal compound.',
'подстроечник тока покоя':'Bias trimmer.'}
WORDS={'Электролитические неполярные':'Non-polar electrolytic','Выпрямительные / сигнальные':'Rectifier / signal','Ответные части разъёмов':'Mating connector parts','Микросхемы и модули':'ICs and modules','Резисторы':'Resistors','Конденсаторы':'Capacitors','Транзисторы':'Transistors','Диоды':'Diodes','Разъёмы':'Connectors','Прочее':'Other','Площадки без деталей':'Pads without parts','Подстроечные':'Trimmers','Керамические':'Ceramic','Плёночные':'Film','Электролитические':'Electrolytic','Стабилитроны':'Zener','Биполярные':'Bipolar','Выходные модули':'Output modules','Микросхемы':'ICs','Стабилизаторы':'Regulators','На плату':'Board-mounted','Для жгута':'Harness','к CN':'for CN','вертикально':'vertical','лёжа на радиаторе':'horizontal on heatsink','лёжа':'horizontal','доработанная v2':'revised v2','отверстия':'holes','радиальный':'radial','площадка':'pad','диск':'disc','шаг':'pitch','мкФ':'uF','кОм':'kohm','МОм':'Mohm','Ом':'ohm','Вт':'W','мм':'mm',' В':' V'}
def translate(s):
 if s in NOTES:return NOTES[s]
 for a,b in WORDS.items():s=s.replace(a,b)
 s=re.sub(r'(?<=\d),(?=\d)', '.',s)
 assert not re.search('[А-Яа-яЁё]',s),s
 return s
rows=list(csv.DictReader((ROOT/'BOM.csv').open(encoding='utf-8-sig'),delimiter=';'))
fields=list(rows[0]);heads=['Category','Group','Qty','References','Value','Power, W','Package / footprint','Manufacturer and part number','+','Notes']
intro='''# Bill of materials — current Cambridge 640A revision

[Русский](BOM.md) · [Project overview](README.en.md) · [Source CSV, Russian](BOM.csv) · [Excel, Russian](BOM.xlsx)

Generated from the same authoritative BOM.csv. **+ means added relative to the factory board**; replacements and larger footprints are not marked as additions. The PCB has 283 positions: 274 fitted components, 2 DNP positions and 7 pads without purchased parts. NT1–NT3 are board copper. Mating connector parts are counted separately.

R88 is 1/4 W; R53/R64/R67/R103 are 1/8 W per the factory BOM, page 23. R68/R116 are 47 ohm, 0.5 W trimmers. All footprint dimensions correspond to the current PCB.

'''
text=intro+'| '+' | '.join(heads)+' |\n| '+' | '.join(['---']*len(heads))+' |\n'
for row in rows:
 text+='| '+' | '.join(translate(row[f]).replace('|','\\|') for f in fields)+' |\n'
text+='''
## Assembly

- Fit U8/U9/U10 and SAP15 modules with the specified heatsink insulation and thermal compound.
- Mount R44/R50 about 3 mm above the board.
- R122/R123: 47 ohm is the starting snubber value for measurement-based adjustment.
- J4 reaches PGND through R97 47 ohm in parallel with C31 100 nF; do not bypass this network.
- [Assembly sequence](doc/assembly-notes/README.en.md) · [First power-up](doc/v2/FIRST_POWER_UP_V2.en.md).
'''
(ROOT/'BOM.en.md').write_text(text)
print('Generated English BOM:',len(rows),'rows')
