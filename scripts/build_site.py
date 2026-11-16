"""Build a bilingual GitHub Pages site from the repository Markdown. Requires markdown2."""
from pathlib import Path,PurePosixPath
import re,shutil,html,os,posixpath
from urllib.parse import urlsplit,unquote
import markdown2
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'_site'
BASE=os.environ.get('PAGES_BASE_PATH','/Cambridge_640A_PowerAmp').rstrip('/')
REPO='https://github.com/SSSound13/Cambridge_640A_PowerAmp'

def destination(path):
 if path=='README.md':return 'index.html'
 if path=='README.en.md':return 'en/index.html'
 return str(PurePosixPath(path).with_suffix('.html'))

def link(path):return BASE+'/'+destination(path)

def build():
 if OUT.exists():shutil.rmtree(OUT)
 OUT.mkdir();shutil.copytree(ROOT/'site/assets',OUT/'assets')
 for d in ['doc','production']:
  shutil.copytree(ROOT/d,OUT/d,ignore=shutil.ignore_patterns('*.md'))
 for pattern in ['*.kicad_*','*.csv','*.xlsx','*.json','*.zip']:
  for p in ROOT.glob(pattern):shutil.copy2(p,OUT/p.name)
 pages=[ROOT/'README.md',ROOT/'README.en.md',ROOT/'BOM.md',ROOT/'BOM.en.md',*sorted((ROOT/'doc').rglob('*.md')),*sorted((ROOT/'production').rglob('*.md'))]
 for source in pages:
  rel=source.relative_to(ROOT).as_posix();en='.en.md' in source.name;lang='en' if en else 'ru'
  rendered=markdown2.markdown(source.read_text(),extras=['tables','fenced-code-blocks','header-ids','strike'])
  title=re.search(r'<h1[^>]*>(.*?)</h1>',rendered,re.S).group(1)
  sibling=rel.replace('.en.md','.md') if en else rel[:-3]+'.en.md'
  if not (ROOT/sibling).exists():sibling='README.md' if en else 'README.en.md'
  rus=link(sibling) if en else link(rel);eng=link(rel) if en else link(sibling)
  def rewrite(m):
   attr,value=m.group(1),html.unescape(m.group(2));parts=urlsplit(value)
   if parts.scheme or parts.netloc:return m.group()
   if not parts.path:return m.group()
   path=posixpath.normpath(posixpath.join(posixpath.dirname(rel),unquote(parts.path)))
   if path.endswith('.md'):path=destination(path)
   url=BASE+'/'+path+('?' + parts.query if parts.query else '')+('#'+parts.fragment if parts.fragment else '')
   return attr+'="'+html.escape(url,quote=True)+'"'
  rendered=re.sub(r'(href|src)="([^"]+)"',rewrite,rendered)
  rendered=re.sub(r'<table>(.*?)</table>',r'<div class="table-wrap" tabindex="0"><table>\1</table></div>',rendered,flags=re.S)
  labels=['Fabrication','Parts list','Assembly','Wiring','First power-up'] if en else ['Производство','Перечень деталей','Сборка платы','Подключение','Первое включение']
  routes=['production/README','BOM','doc/assembly-notes/README','doc/v2/WIRING','doc/v2/FIRST_POWER_UP_V2']
  nav=''.join(f'<a href="{link(p+(".en" if en else "")+".md")}"'+(' aria-current="page"' if rel==p+('.en' if en else '')+'.md' else '')+f'>{label}</a>' for p,label in zip(routes,labels))
  headings=re.findall(r'<h2 id="([^"]+)">(.*?)</h2>',rendered,re.S)
  toc='<details class="toc"><summary>'+('On this page' if en else 'На этой странице')+'</summary><ul>'+''.join('<li><a href="#'+i+'">'+t+'</a></li>' for i,t in headings)+'</ul></details>' if headings else ''
  home=rel in ['README.md','README.en.md']
  metrics=''
  if home:
   metrics='<div class="metricbar">'+''.join(f'<div class="metric"><strong>{v}</strong><span>{t}</span></div>' for v,t in zip(['4','274','1.6 mm','SAP15'],['copper layers','fitted components','board thickness','original output modules'] if en else ['слоя меди','устанавливаемые детали','толщина платы','штатные выходные модули']))+'</div>'
   downloads='<div class="download-strip"><a href="'+BASE+'/production/Cambridge_640A_PowerAmp_production.zip">'+('Download Gerber + drill ZIP' if en else 'Скачать Gerber + сверловку')+'</a><a href="'+link('doc/assembly-notes/README'+('.en' if en else '')+'.md')+'">'+('Assembly documents' if en else 'Документы по сборке')+'</a><a href="'+REPO+'">GitHub ↗</a></div>'
   at=rendered.find('</h1>')+5;rendered=rendered[:at]+metrics+downloads+toc+rendered[at:]
  else:
   at=rendered.find('</h1>')+5;rendered=rendered[:at]+toc+rendered[at:]
  language=f'<div class="languages"><a href="{rus}" lang="ru" hreflang="ru"'+(' aria-current="page"' if not en else '')+'>RU</a><a href="'+eng+'" lang="en" hreflang="en"'+(' aria-current="page"' if en else '')+'>EN</a></div>'
  output=f'''<!doctype html>
<html lang="{lang}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(re.sub('<[^>]+>','',title))} · Cambridge 640A</title><meta name="description" content="{'Four-layer replacement main board for Cambridge Audio Azur 640A V1. PCB, BOM, assembly and fabrication files.' if en else 'Четырёхслойная основная плата Cambridge Audio Azur 640A V1. Исходники, BOM, сборка и производственные файлы.'}"><link rel="stylesheet" href="{BASE}/assets/style.css"><link rel="alternate" hreflang="ru" href="{rus}"><link rel="alternate" hreflang="en" href="{eng}"></head><body>
<a class="skip" href="#content">{'Skip to content' if en else 'Перейти к содержимому'}</a>
<aside class="rail"><a class="brand" href="{link('README.en.md' if en else 'README.md')}"><span>CAMBRIDGE AUDIO</span><strong>Azur 640A</strong><small>{'REPLACEMENT MAIN BOARD' if en else 'НОВАЯ ОСНОВНАЯ ПЛАТА'}</small></a><div class="edition">V1 / AP12707/6<br>4 LAYERS · THT · SAP15</div><nav class="main-nav" aria-label="{'Main navigation' if en else 'Основная навигация'}">{nav}</nav>{language}<a class="repo" href="{REPO}">SSSound13 / Cambridge_640A_PowerAmp ↗</a><details class="mobile-nav"><summary>{'Project navigation' if en else 'Разделы проекта'}</summary><nav class="main-nav">{nav}</nav></details></aside>
<div class="page"><header class="topline"><span>{'Project documentation / current revision' if en else 'Документация проекта / текущая ревизия'}</span><a href="{REPO}">GitHub ↗</a></header><main id="content" class="article">{rendered}</main><footer class="footer">Cambridge Audio Azur 640A V1 · {'Project sources and history' if en else 'Исходники и история проекта'}: <a href="{REPO}">GitHub</a> · RU / EN</footer></div></body></html>'''
  dest=OUT/destination(rel);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(output)
 (OUT/'.nojekyll').write_text('')
 print(f'Built {len(pages)} bilingual documentation pages in {OUT}')
if __name__=='__main__':build()
