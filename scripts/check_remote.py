"""Non-Blender audit of remote library source, pair assets, tracker and V00 scope."""
import csv,sqlite3,sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from pose_common import ROOT,read_json,sha_file
from update_roadmap import save_roadmap

def main():
 p=read_json(ROOT/'project.json');sc=ROOT/p['source_config'];s=read_json(sc)
 cp=sc.parent/s['canonical_catalog'];pair=read_json(ROOT/p['default_pair']['config'])
 with cp.open(encoding='utf-8-sig',newline='') as f:rows=list(csv.DictReader(f))
 metrics={'project_id':p['project_id'],'catalog_sha256_matches':sha_file(cp)==s['catalog_sha256'],
  'records':len(rows),'families':len(set(r['family_id'] for r in rows)),
  'bases':sum(r['variation_code']=='V00' for r in rows),'columns':len(rows[0]),
  'pair_template_exists':(ROOT/'pairs'/pair['pair_id']/pair['version']/'template.blend').is_file(),
  'appearance_template_exists':(ROOT/'pairs'/pair['pair_id']/pair['version']/'studies'/'VP001-v001'/'appearance-study.blend').is_file(),
  'production_enabled':p['production_enabled'],
  'pair_template_sha256_matches':sha_file(ROOT/'pairs'/pair['pair_id']/pair['version']/'template.blend')==pair.get('template_sha256')}
 roadmap=save_roadmap(check=False)
 metrics['roadmap_current']=True
 metrics['v00_accepted']=roadmap['summary']['v00_accepted']
 metrics['v00_built']=roadmap['summary']['v00_built']
 metrics['quality_gates_enabled']=False
 with sqlite3.connect(ROOT/p['tracker']) as db:metrics['job_count']=db.execute('SELECT COUNT(*) FROM jobs').fetchone()[0]
 ok=metrics['catalog_sha256_matches'] and metrics['records']==s['records'] and metrics['families']==s['families'] and metrics['bases']==s['bases'] and metrics['columns']==s['columns'] and metrics['pair_template_exists'] and metrics['pair_template_sha256_matches'] and metrics['roadmap_current']
 print(json.dumps({'ok':ok,**metrics},indent=2))
 if not ok:sys.exit(1)
if __name__=='__main__':main()
