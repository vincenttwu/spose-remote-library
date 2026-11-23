"""Create a data-only SPOSE pose ZIP from a folder of declarative JSON files.

Usage: python scripts/package_pose.py DOGG-DOGG-V00 draft-folder/ --output incoming/
The draft folder needs pose.json, rig-targets.json, contacts.json; optional render-config.json and validation-plan.json.
"""
import argparse,datetime,json,zipfile,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from pose_common import ROOT,source_and_row,read_json,sha_bytes,sha_file,load_package,ALLOWED

def make(pose_id,folder,output,timestamp=None):
 folder=Path(folder);project,src,row=source_and_row(pose_id)
 # Source variation schedule is advisory; all catalog pose IDs may be authored.
 pair=read_json(ROOT/project['default_pair']['config'])
 base=ROOT/'pairs'/pair['pair_id']/pair['version']
 members={p.name:p.read_bytes() for p in folder.iterdir() if p.is_file()}
 if not {'pose.json','rig-targets.json','contacts.json'}.issubset(members) or 'manifest.json' in members or set(members)-ALLOWED:
  raise ValueError('Draft folder must contain only approved JSON payloads')
 if any(not n.endswith('.json') for n in members):raise ValueError('Only JSON files allowed')
 for name,data in members.items():json.loads(data)
 ts=timestamp or datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
 output=Path(output);output.mkdir(parents=True,exist_ok=True)
 dest=output/f'{pose_id}_{ts}.zip'
 if dest.exists():raise FileExistsError(dest)
 manifest={'schema_version':1,'package_type':'spose_pose_module','pose_id':pose_id,'package_timestamp_utc':ts,
  'dependencies':{'source_id':src['source_id'],'source_checkpoint':src['checkpoint'],
  'source_row_sha256':sha_bytes(row['specification'].encode('utf-8')),'pair_id':pair['pair_id'],
  'pair_version':pair['version'],'template_sha256':sha_file(base/'template.blend'),
  'rig_map_id':'RIG001','rig_map_version':'v001'},
  'payload_sha256':{name:sha_bytes(data) for name,data in sorted(members.items())}}
 with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED) as z:
  z.writestr('manifest.json',json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
  for name,data in sorted(members.items()):z.writestr(name,data)
 load_package(dest)
 return dest

def main():
 pa=argparse.ArgumentParser(description=__doc__)
 pa.add_argument('pose_id');pa.add_argument('folder',type=Path)
 pa.add_argument('--output',type=Path,default=ROOT/'incoming')
 pa.add_argument('--timestamp',help='UTC YYYYMMDDTHHMMSSZ override')
 args=pa.parse_args()
 print(make(args.pose_id,args.folder,args.output,args.timestamp))
if __name__=='__main__':main()
