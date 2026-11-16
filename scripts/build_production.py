"""Export and validate the fabrication package with KiCad 10 (KICAD_CLI override supported)."""
from pathlib import Path
import os,subprocess,hashlib,json,zipfile,re
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'production'
CLI=os.environ.get('KICAD_CLI','kicad-cli')
PCB=ROOT/'640A_PowerAmp.kicad_pcb'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run(*args):subprocess.run([CLI,*args],cwd=ROOT,check=True)
def build():
 version=subprocess.check_output([CLI,'version'],text=True).strip()
 if int(version.split('.')[0])<10:raise SystemExit('KiCad 10 or newer is required')
 source_hash=sha(PCB)
 for sub in ['gerbers','drill','validation']:(OUT/sub).mkdir(parents=True,exist_ok=True)
 run('pcb','drc','--format','json','--schematic-parity','--refill-zones','--exit-code-violations','-o','production/validation/drc.json',PCB.name)
 run('pcb','drc','--format','json','--schematic-parity','--severity-all','-o','production/validation/drc_with_exclusions.json',PCB.name)
 run('pcb','export','gerbers','--layers','F.Cu,In1.Cu,In2.Cu,B.Cu,F.Mask,B.Mask,F.Silkscreen,B.Silkscreen,Edge.Cuts','--subtract-soldermask','--check-zones','-o','production/gerbers/',PCB.name)
 run('pcb','export','drill','--format','excellon','--excellon-units','mm','--drill-origin','absolute','--excellon-zeros-format','decimal','--excellon-separate-th','--generate-map','--map-format','pdf','--generate-report','--report-path','production/drill/drill-report.txt','-o','production/drill/',PCB.name)
 drc=json.loads((OUT/'validation/drc.json').read_text())
 assert not drc['violations'] and not drc['unconnected_items'] and not drc['schematic_parity']
 assert source_hash==sha(PCB),'PCB changed during export'
 stack=[('F_Cu.gtl','Copper,L1,Top'),('In1_Cu.g1','Copper,L2,Inr'),('In2_Cu.g2','Copper,L3,Inr'),('B_Cu.gbl','Copper,L4,Bot')]
 for suffix,function in stack:
  text=(OUT/'gerbers'/('640A_PowerAmp-'+suffix)).read_text()
  assert function in text,(suffix,function)
  assert '%MOMM*%' in text and '%TF.SameCoordinates,Original*%' in text
 report=(OUT/'drill/drill-report.txt').read_text()
 assert 'Total plated holes count 648' in report and 'Total unplated holes count 8' in report
 assert len(list((OUT/'gerbers').glob('*')))==10
 files=sorted(p for sub in ['gerbers','drill','validation'] for p in (OUT/sub).iterdir() if p.is_file())
 for extra in ['FABRICATION_NOTES.txt','README.md','README.en.md']:files.append(OUT/extra)
 manifest={'source_pcb':PCB.name,'pcb_sha256':source_hash,'kicad_version':version,'stackup':['F.Cu','In1.Cu','In2.Cu','B.Cu'],'board_mm':[198.9259,129.9597],'thickness_mm':1.6,'copper_um':[70,35,35,70],'origin':'absolute; identical for Gerber and Excellon; no mirroring','pth_holes':648,'npth_holes':8,'vias':0,'active_drc_violations':0,'unconnected_items':0,'schematic_parity_issues':0,'files':{str(p.relative_to(OUT)):sha(p) for p in files}}
 (OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n');files.append(OUT/'manifest.json')
 archive=OUT/'Cambridge_640A_PowerAmp_production.zip'
 with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for p in files:z.write(p,str(p.relative_to(OUT)))
 checks=files+[archive];(OUT/'SHA256SUMS.txt').write_text(''.join(f'{sha(p)}  {p.relative_to(OUT)}\n' for p in checks))
 print(f'Validated fabrication ZIP: {len(files)} files; PCB {source_hash}')
if __name__=='__main__':build()
